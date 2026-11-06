"""Control de acceso por rol (RQF-005/006, escenario TC-SEG-ROL): solo el administrador gestiona roles."""
import uuid

import pytest

from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID

ENDPOINTS_ADMIN = [
    ("GET", "/roles/users"),
    ("GET", "/roles/audit-log"),
    ("POST", f"/roles/{uuid.uuid4()}/promote"),
    ("POST", f"/roles/{uuid.uuid4()}/revert"),
]


@pytest.mark.parametrize("method,path", ENDPOINTS_ADMIN)
def test_sin_token_responde_401(client, method, path):
    assert client.request(method, path).status_code == 401


@pytest.mark.parametrize("method,path", ENDPOINTS_ADMIN)
def test_token_invalido_responde_401(client, method, path):
    assert client.request(method, path, headers={"Authorization": "Bearer inventado"}).status_code == 401


@pytest.mark.parametrize("rol", [MENTEE_ROLE_ID, MENTOR_ROLE_ID])
@pytest.mark.parametrize("method,path", ENDPOINTS_ADMIN)
def test_roles_no_administrador_reciben_403(client, fake_auth, method, path, rol):
    headers = fake_auth.login_as(fake_auth.add_user(rol))
    assert client.request(method, path, headers=headers).status_code == 403


def test_administrador_accede(client, admin):
    _, headers = admin
    assert client.get("/roles/users", headers=headers).status_code == 200


def test_si_auth_service_no_responde_la_sesion_se_considera_invalida(client, fake_auth, admin):
    _, headers = admin
    fake_auth.down = True
    assert client.get("/roles/users", headers=headers).status_code == 401


def test_listar_roles_es_publico_y_devuelve_el_catalogo(client):
    r = client.get("/roles")
    assert r.status_code == 200
    assert {x["name"] for x in r.json()} == {"estudiante", "mentora", "administrador"}


def test_listar_usuarios_reenvia_lo_que_informa_auth(client, fake_auth, admin):
    _, headers = admin
    fake_auth.add_user(MENTEE_ROLE_ID, nombre="Ana")
    r = client.get("/roles/users", headers=headers)
    assert {u["nombre"] for u in r.json()} == {"Admin Uno", "Ana"}


def test_listar_usuarios_falla_con_502_si_auth_rechaza_la_llave_interna(client, fake_auth, admin, monkeypatch):
    from app.core.config import settings
    _, headers = admin
    monkeypatch.setattr(settings, "INTERNAL_SERVICE_KEY", "llave-equivocada")
    assert client.get("/roles/users", headers=headers).status_code == 502
