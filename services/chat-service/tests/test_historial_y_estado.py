"""Historial, lectura y estado de la conversación (RQF-017/018/019/021)."""
import uuid
from datetime import datetime, timezone

from app.core.connection_manager import manager
from app.models.conversation import Conversation
from app.models.last_seen import LastSeen
from app.models.message import Message


def test_endpoints_exigen_token(client, mentor):
    for method, path in (("GET", f"/conversations/{mentor.id}/messages"), ("POST", f"/conversations/{mentor.id}/read"),
                         ("GET", f"/conversations/{mentor.id}/status")):
        assert client.request(method, path).status_code == 401
        assert client.request(method, path, headers={"Authorization": "Bearer mala"}).status_code == 401


def test_sin_mentoria_activa_todo_responde_403(client, mentee, mentor):
    for method, path in (("GET", f"/conversations/{mentor.id}/messages"), ("POST", f"/conversations/{mentor.id}/read"),
                         ("GET", f"/conversations/{mentor.id}/status")):
        assert client.request(method, path, headers=mentee.headers).status_code == 403


def test_un_tercero_no_lee_la_conversacion_de_otros(client, mentee, mentor, otra_mentora, vinculo, conversacion, make_message):
    make_message(mentee, "privado")
    assert client.get(f"/conversations/{mentee.id}/messages", headers=otra_mentora.headers).status_code == 403


def test_historial_en_orden_cronologico(client, mentee, mentor, vinculo, make_message):
    make_message(mentee, "uno")
    make_message(mentor, "dos")
    make_message(mentee, "tres")
    r = client.get(f"/conversations/{mentor.id}/messages", headers=mentee.headers)
    assert r.status_code == 200 and [m["content"] for m in r.json()] == ["uno", "dos", "tres"]


def test_historial_ambos_lados_ven_lo_mismo(client, mentee, mentor, vinculo, make_message):
    make_message(mentee, "hola")
    a = client.get(f"/conversations/{mentor.id}/messages", headers=mentee.headers).json()
    b = client.get(f"/conversations/{mentee.id}/messages", headers=mentor.headers).json()
    assert a == b and len(a) == 1


def test_historial_limite_devuelve_los_mas_recientes_en_orden(client, mentee, mentor, vinculo, make_message):
    for i in range(5):
        make_message(mentee, f"m{i}")
    r = client.get(f"/conversations/{mentor.id}/messages", params={"limit": 2}, headers=mentee.headers)
    assert [m["content"] for m in r.json()] == ["m3", "m4"]


def test_historial_pagina_hacia_atras_con_before(client, mentee, mentor, vinculo, make_message):
    mensajes = [make_message(mentee, f"m{i}") for i in range(5)]
    antes = mensajes[3].created_at.isoformat()
    r = client.get(f"/conversations/{mentor.id}/messages", params={"before": antes, "limit": 2}, headers=mentee.headers)
    assert [m["content"] for m in r.json()] == ["m1", "m2"]


def test_historial_rechaza_limite_mayor_a_100(client, mentee, mentor, vinculo):
    assert client.get(f"/conversations/{mentor.id}/messages", params={"limit": 101}, headers=mentee.headers).status_code == 422


def test_historial_crea_la_conversacion_con_roles_correctos_solo_una_vez(client, db, mentee, mentor, vinculo):
    client.get(f"/conversations/{mentor.id}/messages", headers=mentee.headers)
    client.get(f"/conversations/{mentee.id}/messages", headers=mentor.headers)
    c = db.query(Conversation).one()
    assert c.student_user_id == mentee.id and c.mentor_user_id == mentor.id


def test_historial_vacio(client, mentee, mentor, vinculo):
    assert client.get(f"/conversations/{mentor.id}/messages", headers=mentee.headers).json() == []


def test_marcar_como_leido_solo_afecta_mensajes_del_otro(client, db, mentee, mentor, vinculo, make_message):
    mio = make_message(mentee, "mio")
    suyo = make_message(mentor, "suyo")
    assert client.post(f"/conversations/{mentor.id}/read", headers=mentee.headers).status_code == 204
    db.expire_all()
    assert db.get(Message, suyo.id).read_at is not None
    assert db.get(Message, mio.id).read_at is None


def test_marcar_como_leido_no_pisa_lecturas_anteriores(client, db, mentee, mentor, vinculo, make_message):
    leido = make_message(mentor, "ya leido", read=True)
    antes = leido.read_at
    client.post(f"/conversations/{mentor.id}/read", headers=mentee.headers)
    db.expire_all()
    assert db.get(Message, leido.id).read_at == antes


def test_estado_cuenta_no_leidos_y_presencia(client, mentee, mentor, vinculo, make_message):
    make_message(mentor, "a")
    make_message(mentor, "b")
    make_message(mentor, "c", read=True)
    make_message(mentee, "mio")
    r = client.get(f"/conversations/{mentor.id}/status", headers=mentee.headers).json()
    assert r["unread_count"] == 2 and r["online"] is False and r["last_seen_at"] is None
    manager.active_connections[str(mentor.id)] = [object()]
    assert client.get(f"/conversations/{mentor.id}/status", headers=mentee.headers).json()["online"] is True


def test_estado_devuelve_ultima_conexion(client, db, mentee, mentor, vinculo):
    visto = datetime(2030, 1, 7, 15, 30, tzinfo=timezone.utc)
    db.add(LastSeen(user_id=mentor.id, last_seen_at=visto))
    db.commit()
    r = client.get(f"/conversations/{mentor.id}/status", headers=mentee.headers).json()
    assert datetime.fromisoformat(r["last_seen_at"]) == visto
    assert uuid.UUID(r["conversation_id"])


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
