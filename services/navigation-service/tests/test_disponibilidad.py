"""Bloques de disponibilidad de la mentora (RQF-025)."""
import uuid
from datetime import date, time

from app.models.availability_slot import AvailabilitySlot
from app.models.mentorship import Mentorship

DIA = "2030-01-07"


def crear(client, mentor, inicio="09:00:00", fin="10:00:00", dia=DIA):
    return client.post("/mentors/me/availability", json={"date": dia, "start_time": inicio, "end_time": fin}, headers=mentor.headers)


def test_crear_bloque_libre(client, mentor):
    r = crear(client, mentor)
    assert r.status_code == 201
    assert r.json()["status"] == "libre" and r.json()["mentor_user_id"] == str(mentor.id)


def test_fin_debe_ser_posterior_al_inicio(client, mentor):
    assert crear(client, mentor, "10:00:00", "09:00:00").status_code == 400
    assert crear(client, mentor, "10:00:00", "10:00:00").status_code == 400


def test_bloques_traslapados_se_rechazan(client, mentor):
    assert crear(client, mentor, "09:00:00", "10:00:00").status_code == 201
    assert crear(client, mentor, "09:30:00", "10:30:00").status_code == 409   # cruza el final
    assert crear(client, mentor, "08:30:00", "09:30:00").status_code == 409   # cruza el inicio
    assert crear(client, mentor, "09:15:00", "09:45:00").status_code == 409   # contenido
    assert crear(client, mentor, "08:00:00", "11:00:00").status_code == 409   # envuelve


def test_bloques_contiguos_y_de_otro_dia_se_aceptan(client, mentor):
    assert crear(client, mentor, "09:00:00", "10:00:00").status_code == 201
    assert crear(client, mentor, "10:00:00", "11:00:00").status_code == 201
    assert crear(client, mentor, "08:00:00", "09:00:00").status_code == 201
    assert crear(client, mentor, "09:00:00", "10:00:00", dia="2030-01-08").status_code == 201


def test_el_traslape_solo_cuenta_dentro_de_la_misma_mentora(client, mentor, mentor2):
    assert crear(client, mentor).status_code == 201
    assert crear(client, mentor2).status_code == 201


def test_horas_con_zona_horaria_se_normalizan(client, mentor):
    r = crear(client, mentor, "09:00:00+00:00", "10:00:00+00:00")
    assert r.status_code == 201 and r.json()["start_time"] == "09:00:00"


def test_listar_mis_bloques_ordenados(client, mentor, make_slot):
    make_slot(mentor.id, date(2030, 1, 8), time(9), time(10))
    make_slot(mentor.id, date(2030, 1, 7), time(11), time(12))
    make_slot(mentor.id, date(2030, 1, 7), time(9), time(10))
    r = client.get("/mentors/me/availability", headers=mentor.headers).json()
    assert [(s["date"], s["start_time"]) for s in r] == [("2030-01-07", "09:00:00"), ("2030-01-07", "11:00:00"), ("2030-01-08", "09:00:00")]


def test_vista_publica_solo_muestra_bloques_libres(client, mentee, mentor, make_slot):
    make_slot(mentor.id, inicio=time(9), fin=time(10), status="libre")
    make_slot(mentor.id, inicio=time(10), fin=time(11), status="reservado")
    r = client.get(f"/mentors/{mentor.id}/availability", headers=mentee.headers)
    assert r.status_code == 200 and [s["status"] for s in r.json()] == ["libre"]


def test_eliminar_bloque_propio(client, db, mentor, make_slot):
    s = make_slot(mentor.id)
    assert client.delete(f"/mentors/me/availability/{s.id}", headers=mentor.headers).status_code == 204
    assert db.query(AvailabilitySlot).count() == 0


def test_no_se_elimina_bloque_ajeno_ni_inexistente(client, mentor, mentor2, make_slot):
    s = make_slot(mentor2.id)
    assert client.delete(f"/mentors/me/availability/{s.id}", headers=mentor.headers).status_code == 404
    assert client.delete(f"/mentors/me/availability/{uuid.uuid4()}", headers=mentor.headers).status_code == 404


def test_no_se_elimina_un_bloque_con_mentoria_activa(client, mentor, mentee, make_slot, make_mentorship):
    for estado in ("pendiente", "confirmada"):
        s = make_slot(mentor.id, inicio=time(9 if estado == "pendiente" else 12), fin=time(10 if estado == "pendiente" else 13))
        make_mentorship(mentee.id, mentor.id, s, estado)
        assert client.delete(f"/mentors/me/availability/{s.id}", headers=mentor.headers).status_code == 409


def test_eliminar_bloque_descarta_el_historial_de_solicitudes_canceladas_o_rechazadas(client, db, mentor, mentee, make_slot, make_mentorship):
    s = make_slot(mentor.id)
    make_mentorship(mentee.id, mentor.id, s, "cancelada")
    assert client.delete(f"/mentors/me/availability/{s.id}", headers=mentor.headers).status_code == 204
    assert db.query(Mentorship).count() == 0
