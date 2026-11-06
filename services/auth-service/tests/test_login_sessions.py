"""Inicio de sesión, bloqueo por intentos, refresh con rotación, cierre de sesión y validación de sesión
(RQF-002/003, HU003; escenarios de seguridad del control de sesión)."""
from datetime import datetime, timedelta, timezone

from app.core.config import ADMIN_ROLE_ID, MENTOR_ROLE_ID
from app.core.security import create_access_token, hash_opaque_token
from app.models.login_attempt import LoginAttempt
from app.models.refresh_token import RefreshToken
from tests.conftest import PASSWORD, login


def test_login_exitoso_devuelve_par_de_tokens_y_guarda_solo_el_hash_del_refresh(client, db, make_user):
    make_user()
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["access_token"] and body["refresh_token"]
    stored = db.query(RefreshToken).one()
    assert stored.token_hash == hash_opaque_token(body["refresh_token"])
    assert stored.token_hash != body["refresh_token"]


def test_login_credenciales_invalidas_no_distinguen_usuario_de_clave(client, make_user):
    make_user()
    mal_clave = login(client, password="incorrecta-123")
    no_existe = login(client, email="nadie@pruebas.com")
    assert mal_clave.status_code == no_existe.status_code == 401
    assert mal_clave.json() == no_existe.json()


def test_login_correo_no_verificado_responde_403(client, make_user):
    make_user(verified=False)
    r = login(client)
    assert r.status_code == 403 and "not verified" in r.json()["detail"].lower()


def test_login_cuenta_desactivada_responde_403(client, make_user):
    make_user(active=False)
    assert login(client).status_code == 403


def test_login_registra_intentos_exitosos_y_fallidos(client, db, make_user):
    make_user()
    login(client, password="mala-clave-1")
    login(client)
    rows = db.query(LoginAttempt).order_by(LoginAttempt.created_at).all()
    assert [r.success for r in rows] == [False, True]
    assert all(r.ip_address for r in rows)


def test_cinco_intentos_fallidos_bloquean_incluso_con_la_clave_correcta(client, make_user):
    make_user()
    for _ in range(5):
        assert login(client, password="mala-clave-1").status_code == 401
    r = login(client)  # clave correcta, pero la cuenta está bloqueada
    assert r.status_code == 429
    assert "minuto" in r.json()["detail"]


def test_cuatro_intentos_fallidos_todavia_no_bloquean(client, make_user):
    make_user()
    for _ in range(4):
        login(client, password="mala-clave-1")
    assert login(client).status_code == 200


def test_el_bloqueo_expira_a_los_15_minutos_del_ultimo_fallo(client, db, make_user):
    make_user()
    antes = datetime.now(timezone.utc) - timedelta(minutes=16)
    # Cinco fallos dentro de la ventana de 10 min que ya terminaron hace más de 15 min no deben bloquear.
    for i in range(5):
        db.add(LoginAttempt(email="ana@pruebas.com", ip_address="x", success=False, created_at=antes - timedelta(minutes=i)))
    db.commit()
    assert login(client).status_code == 200


def test_el_bloqueo_es_por_correo_no_global(client, make_user):
    make_user()
    make_user(email="otra@pruebas.com")
    for _ in range(5):
        login(client, password="mala-clave-1")
    assert login(client, email="otra@pruebas.com").status_code == 200


def test_refresh_rota_el_token_y_mantiene_la_familia(client, db, make_user):
    make_user()
    first = login(client).json()
    r = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 200
    second = r.json()
    assert second["refresh_token"] != first["refresh_token"]
    rows = db.query(RefreshToken).all()
    assert len(rows) == 2 and len({x.family_id for x in rows}) == 1
    assert sum(1 for x in rows if x.revoked_at is None) == 1


def test_refresh_con_token_reusado_revoca_toda_la_familia(client, db, make_user):
    make_user()
    first = login(client).json()
    second = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]}).json()
    reuso = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert reuso.status_code == 401 and "reuse" in reuso.json()["detail"].lower()
    # El token legítimo más reciente también quedó revocado.
    assert client.post("/auth/refresh", json={"refresh_token": second["refresh_token"]}).status_code == 401
    db.expire_all()
    assert all(x.revoked_at is not None for x in db.query(RefreshToken).all())


def test_refresh_desconocido_o_vencido_se_rechaza(client, db, make_user):
    make_user()
    assert client.post("/auth/refresh", json={"refresh_token": "no-existe"}).status_code == 401
    tokens = login(client).json()
    row = db.query(RefreshToken).one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()
    r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401 and "expired" in r.json()["detail"].lower()


def test_refresh_de_usuario_desactivado_se_rechaza(client, db, make_user):
    u = make_user()
    tokens = login(client).json()
    u.is_active = False
    db.commit()
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401


def test_logout_revoca_la_familia_y_es_idempotente(client, db, make_user):
    make_user()
    tokens = login(client).json()
    assert client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert client.post("/auth/logout", json={"refresh_token": "desconocido"}).status_code == 204


def test_validate_session_devuelve_identidad_y_rol(client, make_user, auth_header):
    u = make_user(role_id=MENTOR_ROLE_ID)
    r = client.get("/auth/validate-session", headers=auth_header(u))
    assert r.status_code == 200
    assert r.json() == {"valid": True, "user_id": str(u.id), "role_id": str(MENTOR_ROLE_ID)}


def test_validate_session_sin_token_o_con_token_invalido(client):
    assert client.get("/auth/validate-session").status_code == 401
    assert client.get("/auth/validate-session", headers={"Authorization": "Bearer basura"}).status_code == 401


def test_validate_session_token_vencido(client, make_user, monkeypatch):
    from app.core.config import settings
    u = make_user()
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    token = create_access_token(str(u.id), str(u.role_id))
    assert client.get("/auth/validate-session", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_validate_session_usuario_desactivado_o_inexistente(client, db, make_user, auth_header):
    u = make_user()
    headers = auth_header(u)
    u.is_active = False
    db.commit()
    assert client.get("/auth/validate-session", headers=headers).status_code == 401
    db.delete(u)
    db.commit()
    assert client.get("/auth/validate-session", headers=headers).status_code == 401


def test_me_devuelve_el_perfil_sin_datos_sensibles(client, make_user, auth_header):
    u = make_user()
    r = client.get("/auth/me", headers=auth_header(u))
    assert r.status_code == 200
    assert r.json()["email"] == u.email and "password_hash" not in r.json()
    assert client.get("/auth/me").status_code == 401


def test_require_admin_distingue_administrador_de_otros_roles(make_user):
    import pytest
    from fastapi import HTTPException
    from app.core.deps import require_admin

    assert require_admin(make_user(email="a@pruebas.com", role_id=ADMIN_ROLE_ID)).email == "a@pruebas.com"
    with pytest.raises(HTTPException) as exc:
        require_admin(make_user(email="m@pruebas.com", role_id=MENTOR_ROLE_ID))
    assert exc.value.status_code == 403
