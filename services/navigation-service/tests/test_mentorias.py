"""Solicitud, aceptación, rechazo y cancelación de mentorías, configuración de la mentora y límite semanal
(RQF-026, RQF-028, RQF-029; historias HU017–HU026)."""
import uuid
from datetime import date, time, timedelta

from app.models.availability_slot import AvailabilitySlot
from app.models.mentor_settings import MentorSettings
from app.models.mentorship import Mentorship
from app.routers.mentorships import _week_bounds


def solicitar(client, persona, slot):
    return client.post("/mentorships", json={"availability_slot_id": str(slot.id)}, headers=persona.headers)


def estado_slot(db, slot):
    db.expire_all()
    return db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot.id).one().status


# --- configuración de la mentora ---

def test_configuracion_por_defecto_se_crea_al_consultarla(client, db, mentor):
    r = client.get("/mentors/me/settings", headers=mentor.headers)
    assert r.status_code == 200
    assert r.json() == {"mentor_user_id": str(mentor.id), "auto_accept": False, "weekly_limit": 5}
    assert db.query(MentorSettings).count() == 1


def test_mentora_activa_y_desactiva_la_aceptacion_automatica(client, mentor):
    assert client.put("/mentors/me/settings", json={"auto_accept": True}, headers=mentor.headers).json()["auto_accept"] is True
    assert client.get("/mentors/me/settings", headers=mentor.headers).json()["auto_accept"] is True
    assert client.put("/mentors/me/settings", json={"auto_accept": False}, headers=mentor.headers).json()["auto_accept"] is False


def test_la_configuracion_es_por_mentora(client, mentor, mentor2):
    client.put("/mentors/me/settings", json={"auto_accept": True}, headers=mentor.headers)
    assert client.get("/mentors/me/settings", headers=mentor2.headers).json()["auto_accept"] is False


# --- solicitud ---

def test_solicitud_queda_pendiente_y_reserva_el_bloque(client, db, mentee, mentor, make_slot, emails):
    slot = make_slot(mentor.id)
    r = solicitar(client, mentee, slot)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pendiente" and body["confirmed_at"] is None
    assert body["student_user_id"] == str(mentee.id) and body["mentor_user_id"] == str(mentor.id)
    assert estado_slot(db, slot) == "reservado"
    assert emails == []  # aún no hay confirmación


def test_con_aceptacion_automatica_la_mentoria_nace_confirmada_y_envia_dos_correos(client, db, mentee, mentor, make_slot, emails):
    client.put("/mentors/me/settings", json={"auto_accept": True}, headers=mentor.headers)
    slot = make_slot(mentor.id, inicio=time(9, 0), fin=time(10, 30))
    r = solicitar(client, mentee, slot)
    assert r.status_code == 201 and r.json()["status"] == "confirmada" and r.json()["confirmed_at"] is not None
    destinos = {e[0]: e[1] for e in emails}
    assert destinos[mentee.user["email"]] == "Mentora Uno" and destinos[mentor.user["email"]] == "Estudiante Uno"
    assert emails[0][2:] == ("2030-01-07", "09:00", "10:30")


def test_un_fallo_de_correo_no_tumba_la_confirmacion(client, mentee, mentor, make_slot, monkeypatch):
    from app.routers import mentorships

    def boom(*a):
        raise RuntimeError("proveedor caído")
    monkeypatch.setattr(mentorships, "send_mentorship_confirmation", boom)
    client.put("/mentors/me/settings", json={"auto_accept": True}, headers=mentor.headers)
    assert solicitar(client, mentee, make_slot(mentor.id)).json()["status"] == "confirmada"


def test_solicitar_bloque_inexistente_o_ya_reservado(client, mentee, mentee2, mentor, make_slot):
    class Fake:
        id = uuid.uuid4()
    assert solicitar(client, mentee, Fake).status_code == 404
    slot = make_slot(mentor.id)
    assert solicitar(client, mentee, slot).status_code == 201
    assert solicitar(client, mentee2, slot).status_code == 409


def test_limite_semanal_bloquea_nuevas_solicitudes(client, db, mentee, mentor, make_slot, make_mentorship):
    client.put("/mentors/me/settings", json={"auto_accept": True}, headers=mentor.headers)
    db.query(MentorSettings).update({"weekly_limit": 2})
    db.commit()
    for h in (9, 10):
        solicitar(client, mentee, make_slot(mentor.id, inicio=time(h), fin=time(h + 1)))
    r = solicitar(client, mentee, make_slot(mentor.id, inicio=time(12), fin=time(13)))
    assert r.status_code == 409 and "límite" in r.json()["detail"]


def test_el_limite_semanal_cuenta_solo_confirmadas_de_esa_semana(client, db, mentee, mentor, make_slot, make_mentorship):
    db.add(MentorSettings(mentor_user_id=mentor.id, auto_accept=False, weekly_limit=1))
    db.commit()
    otra_semana = make_slot(mentor.id, dia=date(2030, 1, 14))
    make_mentorship(mentee.id, mentor.id, otra_semana, "confirmada")
    pendiente = make_slot(mentor.id, inicio=time(11), fin=time(12))
    make_mentorship(mentee.id, mentor.id, pendiente, "pendiente")
    assert solicitar(client, mentee, make_slot(mentor.id, inicio=time(14), fin=time(15))).status_code == 201


def test_limites_de_semana_son_lunes_a_domingo():
    assert _week_bounds(date(2030, 1, 7)) == (date(2030, 1, 7), date(2030, 1, 13))     # lunes
    assert _week_bounds(date(2030, 1, 13)) == (date(2030, 1, 7), date(2030, 1, 13))    # domingo
    assert _week_bounds(date(2030, 1, 9)) == (date(2030, 1, 7), date(2030, 1, 13))


def test_un_bloque_liberado_puede_volver_a_reservarse(client, db, mentee, mentee2, mentor, make_slot):
    slot = make_slot(mentor.id)
    primera = solicitar(client, mentee, slot).json()
    assert client.post(f"/mentorships/{primera['id']}/cancel", headers=mentee.headers).status_code == 200
    segunda = solicitar(client, mentee2, slot)
    assert segunda.status_code == 201 and segunda.json()["student_user_id"] == str(mentee2.id)
    assert db.query(Mentorship).count() == 1  # la fila cancelada se descartó (clave única del bloque)


# --- respuesta de la mentora ---

def test_mentora_acepta_solicitud_pendiente(client, mentee, mentor, make_slot, make_mentorship, emails):
    m = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id))
    r = client.post(f"/mentorships/{m.id}/accept", headers=mentor.headers)
    assert r.status_code == 200 and r.json()["status"] == "confirmada" and r.json()["confirmed_at"]
    assert len(emails) == 2


def test_no_se_acepta_dos_veces_ni_una_ajena_ni_inexistente(client, mentee, mentor, mentor2, make_slot, make_mentorship):
    m = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id))
    assert client.post(f"/mentorships/{m.id}/accept", headers=mentor2.headers).status_code == 404
    assert client.post(f"/mentorships/{uuid.uuid4()}/accept", headers=mentor.headers).status_code == 404
    assert client.post(f"/mentorships/{m.id}/accept", headers=mentor.headers).status_code == 200
    assert client.post(f"/mentorships/{m.id}/accept", headers=mentor.headers).status_code == 400


def test_aceptar_no_puede_superar_el_limite_semanal(client, db, mentee, mentor, make_slot, make_mentorship):
    db.add(MentorSettings(mentor_user_id=mentor.id, auto_accept=False, weekly_limit=1))
    db.commit()
    make_mentorship(mentee.id, mentor.id, make_slot(mentor.id), "confirmada")
    otra = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id, inicio=time(11), fin=time(12)))
    assert client.post(f"/mentorships/{otra.id}/accept", headers=mentor.headers).status_code == 409


def test_rechazar_libera_el_bloque(client, db, mentee, mentor, make_slot, make_mentorship):
    slot = make_slot(mentor.id)
    m = make_mentorship(mentee.id, mentor.id, slot)
    r = client.post(f"/mentorships/{m.id}/reject", headers=mentor.headers)
    assert r.status_code == 200 and r.json()["status"] == "rechazada"
    assert estado_slot(db, slot) == "libre"
    assert client.post(f"/mentorships/{m.id}/reject", headers=mentor.headers).status_code == 400


def test_rechazar_solicitud_ajena_o_inexistente(client, mentee, mentor, mentor2, make_slot, make_mentorship):
    m = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id))
    assert client.post(f"/mentorships/{m.id}/reject", headers=mentor2.headers).status_code == 404
    assert client.post(f"/mentorships/{uuid.uuid4()}/reject", headers=mentor.headers).status_code == 404


# --- cancelación ---

def test_estudiante_o_mentora_pueden_cancelar_y_el_bloque_vuelve_a_libre(client, db, mentee, mentor, make_slot, make_mentorship):
    for quien, h in ((mentee, 9), (mentor, 11)):
        slot = make_slot(mentor.id, inicio=time(h), fin=time(h + 1))
        m = make_mentorship(mentee.id, mentor.id, slot, "confirmada")
        r = client.post(f"/mentorships/{m.id}/cancel", headers=quien.headers)
        assert r.status_code == 200 and r.json()["status"] == "cancelada"
        assert estado_slot(db, slot) == "libre"


def test_un_tercero_no_puede_cancelar(client, mentee, mentee2, mentor, make_slot, make_mentorship):
    m = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id))
    assert client.post(f"/mentorships/{m.id}/cancel", headers=mentee2.headers).status_code == 404


def test_no_se_cancela_lo_ya_resuelto(client, mentee, mentor, make_slot, make_mentorship):
    for estado, h in (("rechazada", 9), ("cancelada", 10), ("completada", 11)):
        m = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id, inicio=time(h), fin=time(h + 1)), estado)
        assert client.post(f"/mentorships/{m.id}/cancel", headers=mentee.headers).status_code == 400


# --- listados ---

def test_listados_incluyen_nombres_y_horario(client, mentee, mentor, make_slot, make_mentorship):
    make_mentorship(mentee.id, mentor.id, make_slot(mentor.id, inicio=time(9), fin=time(10)))
    de_mentora = client.get("/mentors/me/mentorships", headers=mentor.headers).json()
    de_estudiante = client.get("/students/me/mentorships", headers=mentee.headers).json()
    assert len(de_mentora) == len(de_estudiante) == 1
    item = de_mentora[0]
    assert item["student_nombre"] == "Estudiante Uno" and item["mentor_nombre"] == "Mentora Uno"
    assert (item["slot_date"], item["slot_start_time"], item["slot_end_time"]) == ("2030-01-07", "09:00:00", "10:00:00")


def test_cada_quien_ve_solo_sus_mentorias(client, mentee, mentee2, mentor, mentor2, make_slot, make_mentorship):
    make_mentorship(mentee.id, mentor.id, make_slot(mentor.id))
    assert client.get("/students/me/mentorships", headers=mentee2.headers).json() == []
    assert client.get("/mentors/me/mentorships", headers=mentor2.headers).json() == []


def test_listados_vacios(client, mentee, mentor):
    assert client.get("/students/me/mentorships", headers=mentee.headers).json() == []
    assert client.get("/mentors/me/mentorships", headers=mentor.headers).json() == []


def test_el_listado_se_entrega_sin_nombres_si_auth_no_responde(client, fake_auth, monkeypatch, mentee, mentor, make_slot, make_mentorship):
    from app.routers import mentorships
    make_mentorship(mentee.id, mentor.id, make_slot(mentor.id))

    async def falla():
        raise RuntimeError("auth caído")
    monkeypatch.setattr(mentorships, "list_users_internal", falla)
    item = client.get("/students/me/mentorships", headers=mentee.headers).json()[0]
    assert item["student_nombre"] is None and item["slot_date"] == "2030-01-07"


def test_listado_ordenado_de_mas_reciente_a_mas_antigua(client, mentee, mentor, make_slot, make_mentorship):
    a = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id, inicio=time(9), fin=time(10)))
    b = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id, inicio=time(11), fin=time(12)))
    ids = [m["id"] for m in client.get("/students/me/mentorships", headers=mentee.headers).json()]
    assert ids == [str(b.id), str(a.id)]


# --- endpoint interno que consume chat-service ---

def activa(client, a, b, headers):
    return client.get("/internal/mentorships/active", params={"user_a": str(a), "user_b": str(b)}, headers=headers)


def test_mentoria_activa_solo_si_esta_confirmada_y_en_cualquier_orden(client, db, mentee, mentor, make_slot, make_mentorship):
    from tests.conftest import KEY
    m = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id))   # pendiente
    assert activa(client, mentee.id, mentor.id, KEY).json() == {"active": False}
    m.status = "confirmada"
    db.commit()
    assert activa(client, mentee.id, mentor.id, KEY).json() == {"active": True}
    assert activa(client, mentor.id, mentee.id, KEY).json() == {"active": True}


def test_mentoria_activa_no_cruza_personas(client, mentee, mentee2, mentor, make_slot, make_mentorship):
    from tests.conftest import KEY
    make_mentorship(mentee.id, mentor.id, make_slot(mentor.id), "confirmada")
    assert activa(client, mentee2.id, mentor.id, KEY).json() == {"active": False}


def test_endpoint_interno_exige_llave(client, mentee, mentor):
    assert activa(client, mentee.id, mentor.id, {}).status_code == 422
    assert activa(client, mentee.id, mentor.id, {"X-Internal-Service-Key": "mala"}).status_code == 403


def test_confirmar_no_falla_si_alguna_de_las_dos_personas_ya_no_existe(client, fake_auth, mentee, mentor, make_slot, make_mentorship, emails):
    m = make_mentorship(mentee.id, mentor.id, make_slot(mentor.id))
    del fake_auth.users[mentee.user["id"]]   # la estudiante fue eliminada de Auth antes de la aceptación
    r = client.post(f"/mentorships/{m.id}/accept", headers=mentor.headers)
    assert r.status_code == 200 and r.json()["status"] == "confirmada"
    assert emails == []
