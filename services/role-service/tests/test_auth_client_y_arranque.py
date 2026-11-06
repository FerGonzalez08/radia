"""Cliente HTTP hacia Auth Service y arranque del servicio (sembrado de roles)."""
import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.core import auth_client
from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID


def test_validate_session_devuelve_la_sesion(fake_auth):
    user = fake_auth.add_user(ADMIN_ROLE_ID)
    token = fake_auth.login_as(user)["Authorization"].removeprefix("Bearer ")
    assert asyncio.run(auth_client.validate_session(token))["user_id"] == user["id"]


def test_validate_session_token_rechazado_lanza_401(fake_auth):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_client.validate_session("desconocido"))
    assert exc.value.status_code == 401


def test_update_user_role_propaga_404_y_convierte_otros_errores_en_502(fake_auth):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_client.update_user_role_internal("00000000-0000-0000-0000-000000000000", str(MENTOR_ROLE_ID)))
    assert exc.value.status_code == 404
    fake_auth.down = True
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_client.update_user_role_internal("x", str(MENTOR_ROLE_ID)))
    assert exc.value.status_code == 502


def test_list_users_internal_envia_la_llave_interna(fake_auth):
    fake_auth.add_user(MENTEE_ROLE_ID)
    assert len(asyncio.run(auth_client.list_users_internal())) == 1


def test_el_arranque_siembra_los_tres_roles_con_ids_fijos_y_es_idempotente(db):
    from app.main import seed_roles
    db.execute(text("TRUNCATE roles CASCADE"))
    db.commit()
    seed_roles()
    seed_roles()
    rows = dict(db.execute(text("SELECT id::text, name FROM roles")).all())
    assert rows == {str(MENTEE_ROLE_ID): "estudiante", str(MENTOR_ROLE_ID): "mentora", str(ADMIN_ROLE_ID): "administrador"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
