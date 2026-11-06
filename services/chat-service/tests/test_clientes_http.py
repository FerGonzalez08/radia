"""Clientes hacia Auth Service y Navigation Service."""
import asyncio

import pytest
from fastapi import HTTPException

from app.core import clients


def test_validate_session_ok_y_rechazada(fake_auth, mentee):
    assert asyncio.run(clients.validate_session(mentee.token))["user_id"] == str(mentee.id)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(clients.validate_session("desconocido"))
    assert exc.value.status_code == 401


def test_has_active_mentorship_verdadero_y_falso(fake_auth, mentee, mentor, vinculo):
    assert asyncio.run(clients.has_active_mentorship(str(mentee.id), str(mentor.id))) is True
    assert asyncio.run(clients.has_active_mentorship(str(mentor.id), str(mentee.id))) is True
    assert asyncio.run(clients.has_active_mentorship(str(mentee.id), "otra-persona")) is False


def test_has_active_mentorship_falla_cerrado_si_navigation_no_responde(fake_auth, mentee, mentor, vinculo):
    """Si el servicio de navegación falla, el chat NO debe abrirse: se asume que no hay mentoría activa."""
    fake_auth.nav_down = True
    assert asyncio.run(clients.has_active_mentorship(str(mentee.id), str(mentor.id))) is False


def test_has_active_mentorship_envia_la_llave_interna(fake_auth, mentee, mentor, vinculo, monkeypatch):
    monkeypatch.setattr(clients.settings, "INTERNAL_SERVICE_KEY", "llave-equivocada")
    assert asyncio.run(clients.has_active_mentorship(str(mentee.id), str(mentor.id))) is False
