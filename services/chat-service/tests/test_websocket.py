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
