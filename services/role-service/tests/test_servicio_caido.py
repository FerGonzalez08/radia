"""TC-RES-01 / TC-RES-02: si el servicio de autenticación no responde, el servicio responde 503 y no un 500 sin controlar."""
import asyncio

import httpx
import pytest
from fastapi import HTTPException

from app.core import auth_client as clientes


def test_validate_session_devuelve_503_si_auth_esta_caido(monkeypatch):
    async def caido(self, *a, **k):
        raise httpx.ConnectError("conexión rechazada")

    monkeypatch.setattr(httpx.AsyncClient, "request", caido)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(clientes.validate_session("token"))
    assert exc.value.status_code == 503


def test_validate_session_sigue_dando_401_si_el_token_es_invalido(monkeypatch):
    async def invalido(self, *a, **k):
        return httpx.Response(401, json={"detail": "x"})

    monkeypatch.setattr(httpx.AsyncClient, "request", invalido)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(clientes.validate_session("token"))
    assert exc.value.status_code == 401
