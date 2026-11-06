"""Recuperación de contraseña y endpoints internos entre servicios (RQF-004; control de llave interna)."""
from datetime import datetime, timedelta, timezone

from app.core.config import MENTOR_ROLE_ID, MENTEE_ROLE_ID
from app.core.security import verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.verification_token import VerificationToken
from tests.conftest import PASSWORD, login

KEY = {"X-Internal-Service-Key": "clave-interna-pruebas"}


def test_solicitud_de_reset_responde_204_exista_o_no_el_correo(client, make_user, sent_emails):
    make_user()
    assert client.post("/auth/password-reset/request", json={"email": "ana@pruebas.com"}).status_code == 204
    assert client.post("/auth/password-reset/request", json={"email": "nadie@pruebas.com"}).status_code == 204
    assert [e[0] for e in sent_emails] == ["reset"]  # solo se envía para la cuenta real


def test_solicitud_de_reset_no_revela_cuentas_si_falla_el_correo(client, make_user, monkeypatch):
    from app.routers import auth as auth_router
    make_user()

    def boom(*a, **k):
        raise RuntimeError("proveedor caído")
    monkeypatch.setattr(auth_router, "send_password_reset_email", boom)
    assert client.post("/auth/password-reset/request", json={"email": "ana@pruebas.com"}).status_code == 204


def test_reset_crea_token_de_15_minutos_de_tipo_password_reset(client, db, make_user, sent_emails):
    make_user()
    client.post("/auth/password-reset/request", json={"email": "ana@pruebas.com"})
    rec = db.query(VerificationToken).one()
    assert rec.type == "password_reset"
    restante = rec.expires_at - datetime.now(timezone.utc)
    assert timedelta(minutes=14) < restante <= timedelta(minutes=15)


def test_confirmar_reset_cambia_la_clave_y_revoca_todas_las_sesiones(client, db, make_user, make_token_record):
    u = make_user()
    login(client)
    login(client)
    make_token_record(u.id, "reset-1", type_="password_reset")
    r = client.post("/auth/password-reset/confirm", json={"token": "reset-1", "new_password": "Nueva-Clave-99"})
    assert r.status_code == 204
    db.expire_all()
    assert verify_password("Nueva-Clave-99", db.query(User).filter(User.id == u.id).one().password_hash)
    assert all(x.revoked_at is not None for x in db.query(RefreshToken).all())
    assert login(client, password=PASSWORD).status_code == 401
    assert login(client, password="Nueva-Clave-99").status_code == 200


def test_confirmar_reset_token_invalido_reusado_vencido_o_de_otro_tipo(client, make_user, make_token_record):
    u = make_user()
    make_token_record(u.id, "usado", type_="password_reset", used=True)
    make_token_record(u.id, "vencido", type_="password_reset", expires_in=timedelta(seconds=-1))
    make_token_record(u.id, "verif", type_="email_verification")
    for tok in ("no-existe", "usado", "vencido", "verif"):
        r = client.post("/auth/password-reset/confirm", json={"token": tok, "new_password": "Nueva-Clave-99"})
        assert r.status_code == 400, tok


def test_confirmar_reset_exige_clave_nueva_de_longitud_minima(client, make_user, make_token_record):
    u = make_user()
    make_token_record(u.id, "reset-2", type_="password_reset")
    assert client.post("/auth/password-reset/confirm", json={"token": "reset-2", "new_password": "corta"}).status_code == 422


def test_el_token_de_reset_es_de_un_solo_uso(client, make_user, make_token_record):
    u = make_user()
    make_token_record(u.id, "reset-3", type_="password_reset")
    body = {"token": "reset-3", "new_password": "Nueva-Clave-99"}
    assert client.post("/auth/password-reset/confirm", json=body).status_code == 204
    assert client.post("/auth/password-reset/confirm", json=body).status_code == 400


# --- Endpoints internos (consumidos por role-service y navigation-service) ---

def test_internos_exigen_la_llave_de_servicio(client, make_user):
    u = make_user()
    assert client.get("/internal/users").status_code == 422                       # falta el encabezado
    assert client.get("/internal/users", headers={"X-Internal-Service-Key": "mala"}).status_code == 403
    assert client.patch(f"/internal/users/{u.id}/role", json={"role_id": str(MENTOR_ROLE_ID)},
                        headers={"X-Internal-Service-Key": "mala"}).status_code == 403


def test_un_access_token_de_usuario_no_sirve_como_llave_interna(client, make_user, auth_header):
    u = make_user()
    assert client.get("/internal/users", headers=auth_header(u)).status_code == 422


def test_listar_usuarios_interno(client, make_user):
    make_user(email="a@pruebas.com")
    make_user(email="b@pruebas.com")
    r = client.get("/internal/users", headers=KEY)
    assert r.status_code == 200 and {u["email"] for u in r.json()} == {"a@pruebas.com", "b@pruebas.com"}
    assert all("password_hash" not in u for u in r.json())


def test_cambiar_rol_interno(client, db, make_user):
    u = make_user()
    r = client.patch(f"/internal/users/{u.id}/role", json={"role_id": str(MENTOR_ROLE_ID)}, headers=KEY)
    assert r.status_code == 200 and r.json()["role_id"] == str(MENTOR_ROLE_ID)
    db.expire_all()
    assert db.query(User).filter(User.id == u.id).one().role_id == MENTOR_ROLE_ID


def test_cambiar_rol_de_usuario_inexistente(client):
    import uuid
    r = client.patch(f"/internal/users/{uuid.uuid4()}/role", json={"role_id": str(MENTEE_ROLE_ID)}, headers=KEY)
    assert r.status_code == 404


def test_el_cambio_de_rol_se_refleja_de_inmediato_en_validate_session(client, make_user):
    """validate-session consulta el rol en la base de datos, no en el JWT: tras promover a una usuaria, los demás
    servicios ven el rol nuevo con el mismo access token, sin esperar a que expire."""
    u = make_user()
    token = login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/auth/validate-session", headers=headers).json()["role_id"] == str(MENTEE_ROLE_ID)
    client.patch(f"/internal/users/{u.id}/role", json={"role_id": str(MENTOR_ROLE_ID)}, headers=KEY)
    assert client.get("/auth/validate-session", headers=headers).json()["role_id"] == str(MENTOR_ROLE_ID)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
