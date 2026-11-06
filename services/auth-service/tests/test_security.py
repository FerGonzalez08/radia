"""Pruebas unitarias de app.core.security: contraseñas, JWT y tokens opacos (RNF de seguridad, control de sesión)."""
import time

import pytest
from jose import jwt

from app.core import security
from app.core.config import settings


def test_hash_password_no_guarda_texto_plano_y_verifica():
    hashed = security.hash_password("Secreta-123")
    assert hashed != "Secreta-123"
    assert security.verify_password("Secreta-123", hashed) is True
    assert security.verify_password("otra", hashed) is False


def test_hash_password_usa_sal_distinta_en_cada_llamada():
    assert security.hash_password("Secreta-123") != security.hash_password("Secreta-123")


def test_pre_hash_sha256_evita_el_truncamiento_de_72_bytes():
    base = "a" * 80
    hashed = security.hash_password(base)
    # Con bcrypt sin pre-hash, estas dos contraseñas (iguales en los primeros 72 bytes) coincidirían.
    assert security.verify_password(base + "distinto", hashed) is False
    assert security.verify_password(base, hashed) is True


def test_access_token_ida_y_vuelta_conserva_identidad_y_rol():
    token = security.create_access_token("user-1", "role-1")
    payload = security.decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role_id"] == "role-1"
    assert payload["exp"] > payload["iat"]


def test_access_token_expira(monkeypatch):
    monkeypatch.setattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    token = security.create_access_token("user-1", "role-1")
    assert security.decode_access_token(token) is None


def test_access_token_con_firma_alterada_se_rechaza():
    token = security.create_access_token("user-1", "role-1")
    assert security.decode_access_token(token + "x") is None


def test_access_token_firmado_con_otra_clave_se_rechaza():
    forged = jwt.encode({"sub": "user-1", "role_id": "admin", "exp": int(time.time()) + 600}, "otra-clave", algorithm="HS256")
    assert security.decode_access_token(forged) is None


def test_access_token_con_algoritmo_none_se_rechaza():
    # Ataque clásico: token sin firma. decode debe exigir el algoritmo configurado.
    unsigned = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyLTEifQ."
    assert security.decode_access_token(unsigned) is None


@pytest.mark.parametrize("basura", ["", "no-es-un-jwt", "a.b.c"])
def test_access_token_malformado_devuelve_none(basura):
    assert security.decode_access_token(basura) is None


def test_token_opaco_es_aleatorio_y_su_hash_es_estable():
    a, b = security.generate_opaque_token(), security.generate_opaque_token()
    assert a != b and len(a) >= 48
    assert security.hash_opaque_token(a) == security.hash_opaque_token(a)
    assert security.hash_opaque_token(a) != a
    assert len(security.hash_opaque_token(a)) == 64
