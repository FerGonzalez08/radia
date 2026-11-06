"""Control de acceso por rol en el servicio de navegación (menú/funciones por rol; escenarios TC-SEG-ROL y FRT-02)."""
import uuid

import pytest

SIN_AUTENTICAR = [
    ("GET", "/categories"), ("POST", "/categories"), ("GET", "/mentors/me/availability"),
    ("POST", "/mentors/me/availability"), ("GET", "/mentors/me/settings"), ("GET", "/mentors/me/mentorships"),
    ("GET", "/students/me/mentorships"), ("POST", "/mentorships"), ("GET", "/search/mentors"),
    ("GET", f"/mentors/{uuid.uuid4()}/availability"), ("PUT", "/mentors/me/categories"),
]
SOLO_MENTORA = [
    ("GET", "/mentors/me/availability"), ("POST", "/mentors/me/availability"),
    ("DELETE", f"/mentors/me/availability/{uuid.uuid4()}"), ("GET", "/mentors/me/settings"),
    ("PUT", "/mentors/me/settings"), ("GET", "/mentors/me/mentorships"), ("GET", "/mentors/me/categories"),
    ("PUT", "/mentors/me/categories"), ("POST", f"/mentorships/{uuid.uuid4()}/accept"),
    ("POST", f"/mentorships/{uuid.uuid4()}/reject"),
]
SOLO_ADMIN = [
    ("POST", "/categories"), ("PUT", f"/categories/{uuid.uuid4()}"), ("DELETE", f"/categories/{uuid.uuid4()}"),
]


@pytest.mark.parametrize("method,path", SIN_AUTENTICAR)
def test_sin_token_responde_401(client, method, path):
    assert client.request(method, path).status_code == 401


@pytest.mark.parametrize("method,path", SIN_AUTENTICAR)
def test_token_invalido_responde_401(client, method, path):
    assert client.request(method, path, headers={"Authorization": "Bearer inventado"}).status_code == 401


@pytest.mark.parametrize("method,path", SOLO_MENTORA)
def test_endpoints_de_mentora_prohiben_a_estudiantes_y_administradores(client, mentee, admin, method, path):
    assert client.request(method, path, headers=mentee.headers).status_code == 403
    assert client.request(method, path, headers=admin.headers).status_code == 403


@pytest.mark.parametrize("method,path", SOLO_ADMIN)
def test_endpoints_de_catalogo_prohiben_a_estudiantes_y_mentoras(client, mentee, mentor, method, path):
    assert client.request(method, path, headers=mentee.headers).status_code == 403
    assert client.request(method, path, headers=mentor.headers).status_code == 403


def test_solo_un_estudiante_puede_solicitar_mentoria(client, mentor, admin, make_slot, mentor2):
    slot = make_slot(mentor2.id)
    body = {"availability_slot_id": str(slot.id)}
    assert client.post("/mentorships", json=body, headers=mentor.headers).status_code == 403
    assert client.post("/mentorships", json=body, headers=admin.headers).status_code == 403


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
