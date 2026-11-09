"""Chat en tiempo real por WebSocket (RQF-016, RQF-019, RQF-022): autenticación, mentoría activa, entrega, acuse y presencia."""
import pytest
from starlette.websockets import WebSocketDisconnect

from app.models.last_seen import LastSeen
from app.models.message import Message


def ws_url(otro, token):
    return f"/ws/{otro.id}?token={token}"


def test_token_invalido_cierra_con_4401(client, mentor):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/{mentor.id}?token=invalido"):
            pass
    assert exc.value.code == 4401


def test_sin_token_la_conexion_se_rechaza(client, mentor):
    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/{mentor.id}"):
            pass


def test_sin_mentoria_activa_cierra_con_4403_y_no_deja_rastro(client, db, mentee, mentor):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(ws_url(mentor, mentee.token)):
            pass
    assert exc.value.code == 4403
    assert db.query(Message).count() == 0


def test_mensaje_con_destinatario_desconectado_queda_enviado_y_persistido(client, db, mentee, mentor, vinculo):
    with client.websocket_connect(ws_url(mentor, mentee.token)) as ws:
        ws.send_json({"content": "  Hola, mentora  "})
        ack = ws.receive_json()
    assert ack["type"] == "ack" and ack["status"] == "enviado"
    m = db.query(Message).one()
    assert m.content == "Hola, mentora" and m.status == "enviado" and m.sender_user_id == mentee.id
    assert str(m.id) == ack["id"]


def test_mensajes_vacios_o_sin_contenido_se_ignoran(client, db, mentee, mentor, vinculo):
    with client.websocket_connect(ws_url(mentor, mentee.token)) as ws:
        ws.send_json({"content": ""})
        ws.send_json({"content": "   "})
        ws.send_json({})
        ws.send_json({"content": "real"})
        assert ws.receive_json()["type"] == "ack"
    assert [m.content for m in db.query(Message).all()] == ["real"]


def test_mensaje_con_destinatario_conectado_se_entrega_en_tiempo_real(client, db, mentee, mentor, vinculo):
    with client.websocket_connect(ws_url(mentee, mentor.token)) as ws_mentora:
        with client.websocket_connect(ws_url(mentor, mentee.token)) as ws_estudiante:
            assert ws_mentora.receive_json() == {"type": "presence", "user_id": str(mentee.id), "online": True}
            ws_estudiante.send_json({"content": "¿Puedes revisar mi CV?"})
            recibido = ws_mentora.receive_json()
            ack = ws_estudiante.receive_json()
    assert recibido["type"] == "message" and recibido["content"] == "¿Puedes revisar mi CV?"
    assert recibido["sender_user_id"] == str(mentee.id)
    assert ack["status"] == "entregado"
    db.expire_all()
    m = db.query(Message).one()
    assert m.status == "entregado" and str(m.id) == recibido["id"] == ack["id"]


def test_la_conversacion_usa_el_rol_para_asignar_estudiante_y_mentora(client, db, mentee, mentor, vinculo):
    from app.models.conversation import Conversation
    with client.websocket_connect(ws_url(mentee, mentor.token)):
        pass
    c = db.query(Conversation).one()
    assert c.student_user_id == mentee.id and c.mentor_user_id == mentor.id


def test_al_desconectar_la_ultima_sesion_se_guarda_last_seen_y_se_avisa(client, db, mentee, mentor, vinculo):
    with client.websocket_connect(ws_url(mentee, mentor.token)) as ws_mentora:
        with client.websocket_connect(ws_url(mentor, mentee.token)):
            assert ws_mentora.receive_json()["online"] is True
        aviso = ws_mentora.receive_json()
    assert aviso["type"] == "presence" and aviso["online"] is False and aviso["user_id"] == str(mentee.id)
    assert aviso["last_seen_at"]
    assert db.query(LastSeen).filter(LastSeen.user_id == mentee.id).one().last_seen_at is not None


def test_last_seen_se_actualiza_en_lugar_de_duplicarse(client, db, mentee, mentor, vinculo):
    for _ in range(2):
        with client.websocket_connect(ws_url(mentor, mentee.token)):
            pass
    assert db.query(LastSeen).filter(LastSeen.user_id == mentee.id).count() == 1


def test_cerrar_una_pestana_no_marca_desconexion_si_queda_otra(client, db, mentee, mentor, vinculo):
    with client.websocket_connect(ws_url(mentee, mentor.token)) as ws_mentora:
        with client.websocket_connect(ws_url(mentor, mentee.token)):
            with client.websocket_connect(ws_url(mentor, mentee.token)):
                pass
            assert db.query(LastSeen).filter(LastSeen.user_id == mentee.id).count() == 0
        assert [m["online"] for m in (ws_mentora.receive_json(), ws_mentora.receive_json(), ws_mentora.receive_json())
                if m["type"] == "presence"].count(False) == 1


def test_mensajes_persisten_entre_conexiones(client, db, mentee, mentor, vinculo):
    with client.websocket_connect(ws_url(mentor, mentee.token)) as ws:
        ws.send_json({"content": "uno"})
        ws.receive_json()
    with client.websocket_connect(ws_url(mentor, mentee.token)) as ws:
        ws.send_json({"content": "dos"})
        ws.receive_json()
    assert [m.content for m in db.query(Message).order_by(Message.created_at)] == ["uno", "dos"]
    r = client.get(f"/conversations/{mentor.id}/messages", headers=mentee.headers)
    assert [m["content"] for m in r.json()] == ["uno", "dos"]


def test_las_conexiones_inactivas_no_retienen_conexiones_del_pool(client, db, fake_auth, mentor):
    """DEF-001 / TC-NFR-02: 20 usuarias conectadas sin escribir (más que las 15 del pool) no agotan la base de datos."""
    from contextlib import ExitStack
    from app.core.database import engine
    from app.models.message import Message as Mensaje
    from app.core.config import MENTEE_ROLE_ID

    with ExitStack() as stack:
        sockets = []
        for _ in range(20):
            u = fake_auth.add_user(MENTEE_ROLE_ID)
            fake_auth.mentorships.add(frozenset((u["id"], str(mentor.id))))
            token = fake_auth.login_as(u)["Authorization"].removeprefix("Bearer ")
            sockets.append(stack.enter_context(client.websocket_connect(f"/ws/{mentor.id}?token={token}")))
        assert engine.pool.checkedout() == 0
        # El servicio sigue pudiendo usar la base de datos con 20 conexiones abiertas.
        sockets[0].send_json({"content": "hola"})
        assert sockets[0].receive_json()["type"] == "ack"
        assert db.query(Mensaje).count() == 1


def test_mensajes_por_encima_del_limite_por_minuto_se_rechazan(client, db, mentee, mentor, vinculo, monkeypatch):
    """TC-CHT-13 / ASR-25: pasado el umbral se rechaza con error controlado y no se guarda."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "MESSAGES_PER_MINUTE", 5)
    with client.websocket_connect(ws_url(mentor, mentee.token)) as ws:
        respuestas = []
        for i in range(8):
            ws.send_json({"content": f"mensaje {i}"})
            respuestas.append(ws.receive_json())
    assert [r["type"] for r in respuestas] == ["ack"] * 5 + ["error"] * 3
    assert respuestas[-1]["code"] == "rate_limited" and respuestas[-1]["retry_after"] >= 1
    assert db.query(Message).count() == 5


def test_el_limite_de_una_usuaria_no_afecta_a_otra(client, db, mentee, mentor, vinculo, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "MESSAGES_PER_MINUTE", 2)
    with client.websocket_connect(ws_url(mentor, mentee.token)) as w_mentee:
        for i in range(3):
            w_mentee.send_json({"content": f"m{i}"})
            w_mentee.receive_json()
        with client.websocket_connect(ws_url(mentee, mentor.token)) as w_mentor:
            w_mentor.send_json({"content": "respuesta"})
            assert w_mentor.receive_json()["type"] == "ack"


def test_mensaje_de_mas_de_2000_caracteres_da_error_controlado(client, db, mentee, mentor, vinculo):
    """TC-CHT-04: error controlado; la conexión sigue abierta y no se guarda el mensaje."""
    with client.websocket_connect(ws_url(mentor, mentee.token)) as ws:
        ws.send_json({"content": "x" * 2001})
        err = ws.receive_json()
        ws.send_json({"content": "x" * 2000})
        ok = ws.receive_json()
    assert err["type"] == "error" and err["code"] == "message_too_long"
    assert ok["type"] == "ack"
    assert db.query(Message).count() == 1
