"""Cliente hacia Auth Service, correo de confirmación y sembrado de categorías."""
import asyncio
import sys
import types

import pytest
from fastapi import HTTPException

from app.core import auth_client, mailer
from app.core import email as email_templates
from app.core.config import MENTEE_ROLE_ID, settings


def test_validate_session_rechazada_lanza_401(fake_auth):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_client.validate_session("desconocido"))
    assert exc.value.status_code == 401


def test_list_users_internal_falla_con_502_si_auth_no_esta_disponible(fake_auth):
    fake_auth.down = True
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth_client.list_users_internal())
    assert exc.value.status_code == 502


def test_get_user_encuentra_o_devuelve_none(fake_auth):
    u = fake_auth.add_user(MENTEE_ROLE_ID, nombre="Ana")
    assert asyncio.run(auth_client.get_user(u["id"]))["nombre"] == "Ana"
    assert asyncio.run(auth_client.get_user("no-existe")) is None


def test_plantilla_de_confirmacion_incluye_los_datos_de_la_mentoria(monkeypatch):
    capturado = []
    monkeypatch.setattr(email_templates, "send_email", lambda to, subject, html: capturado.append((to, subject, html)))
    email_templates.send_mentorship_confirmation("a@b.com", "Mentora Uno", "2030-01-07", "09:00", "10:00")
    to, subject, html = capturado[0]
    assert to == "a@b.com" and "confirmada" in subject.lower()
    assert "Mentora Uno" in html and "2030-01-07" in html and "09:00 - 10:00" in html


def test_mailer_selecciona_proveedor_y_relanza_errores(monkeypatch):
    llamadas = []
    monkeypatch.setattr(mailer, "_send_resend", lambda *a: llamadas.append("resend"))
    monkeypatch.setattr(mailer, "_send_acs", lambda *a: llamadas.append("acs"))
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    mailer.send_email("a@b.com", "x", "y")
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "acs")
    mailer.send_email("a@b.com", "x", "y")
    assert llamadas == ["resend", "acs"]

    def boom(*a):
        raise RuntimeError("caído")
    monkeypatch.setattr(mailer, "_send_acs", boom)
    with pytest.raises(RuntimeError):
        mailer.send_email("a@b.com", "x", "y")


def test_plain_text_y_proveedores_concretos(monkeypatch):
    assert mailer._plain_text("<p>Hola</p><p>Mundo<br>otra</p>") == "Hola\nMundo\notra"

    enviados = []
    fake = types.ModuleType("resend")
    fake.Emails = types.SimpleNamespace(send=lambda payload: enviados.append(payload))
    monkeypatch.setitem(sys.modules, "resend", fake)
    mailer._send_resend("a@b.com", "Asunto", "<p>x</p>")
    assert enviados[0]["to"] == "a@b.com"

    monkeypatch.setattr(settings, "ACS_CONNECTION_STRING", "")
    monkeypatch.setattr(settings, "ACS_SENDER_ADDRESS", "")
    with pytest.raises(RuntimeError):
        mailer._send_acs("a@b.com", "x", "<p>y</p>")

    mensajes = []

    class FakeClient:
        @classmethod
        def from_connection_string(cls, cs):
            return cls()

        def begin_send(self, message):
            mensajes.append(message)

    for nombre in ("azure", "azure.communication"):
        monkeypatch.setitem(sys.modules, nombre, types.ModuleType(nombre))
    mail = types.ModuleType("azure.communication.email")
    mail.EmailClient = FakeClient
    monkeypatch.setitem(sys.modules, "azure.communication.email", mail)
    monkeypatch.setattr(settings, "ACS_CONNECTION_STRING", "endpoint=x")
    monkeypatch.setattr(settings, "ACS_SENDER_ADDRESS", "no-reply@x")
    mailer._send_acs("a@b.com", "Asunto", "<p>Hola</p>")
    assert mensajes[0]["content"]["plainText"] == "Hola"


def test_el_arranque_siembra_categorias_sin_duplicar(db):
    from app.main import seed_categories
    from app.models.category import Category
    seed_categories()
    seed_categories()
    nombres = {c.name for c in db.query(Category).all()}
    assert nombres == {"Python", "JavaScript", "React", "Java", "Bases de datos", "Diseño UX/UI"}
    assert db.query(Category).count() == 6
