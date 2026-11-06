"""Selección de proveedor de correo (Resend / Azure Communication Services) y plantillas."""
import sys
import types

import pytest

from app.core import email as email_templates
from app.core import mailer
from app.core.config import settings


def test_plain_text_quita_etiquetas_y_conserva_saltos():
    assert mailer._plain_text("<p>Hola</p><p>Mundo<br>otra</p>") == "Hola\nMundo\notra"


def test_send_email_usa_resend_por_defecto(monkeypatch):
    llamadas = []
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(mailer, "_send_resend", lambda *a: llamadas.append(("resend", a)))
    monkeypatch.setattr(mailer, "_send_acs", lambda *a: llamadas.append(("acs", a)))
    mailer.send_email("a@b.c", "Asunto", "<p>x</p>")
    assert llamadas == [("resend", ("a@b.c", "Asunto", "<p>x</p>"))]


def test_send_email_usa_acs_cuando_se_configura(monkeypatch):
    llamadas = []
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "acs")
    monkeypatch.setattr(mailer, "_send_acs", lambda *a: llamadas.append(a))
    mailer.send_email("a@b.c", "Asunto", "<p>x</p>")
    assert llamadas == [("a@b.c", "Asunto", "<p>x</p>")]


def test_send_email_relanza_el_error_del_proveedor(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")

    def boom(*a):
        raise RuntimeError("caído")
    monkeypatch.setattr(mailer, "_send_resend", boom)
    with pytest.raises(RuntimeError):
        mailer.send_email("a@b.c", "x", "y")


def test_send_resend_construye_el_mensaje(monkeypatch):
    enviados = []
    fake = types.ModuleType("resend")
    fake.Emails = types.SimpleNamespace(send=lambda payload: enviados.append(payload))
    monkeypatch.setitem(sys.modules, "resend", fake)
    mailer._send_resend("a@b.c", "Asunto", "<p>x</p>")
    assert enviados[0]["to"] == "a@b.c" and enviados[0]["from"] == settings.RESEND_SENDER_EMAIL
    assert fake.api_key == settings.RESEND_API_KEY


def test_send_acs_exige_configuracion(monkeypatch):
    monkeypatch.setattr(settings, "ACS_CONNECTION_STRING", "")
    monkeypatch.setattr(settings, "ACS_SENDER_ADDRESS", "")
    with pytest.raises(RuntimeError):
        mailer._send_acs("a@b.c", "x", "<p>y</p>")


def test_send_acs_no_espera_el_resultado(monkeypatch):
    mensajes = []

    class FakeClient:
        @classmethod
        def from_connection_string(cls, cs):
            return cls()

        def begin_send(self, message):
            mensajes.append(message)

    pkg = types.ModuleType("azure")
    comm = types.ModuleType("azure.communication")
    mail = types.ModuleType("azure.communication.email")
    mail.EmailClient = FakeClient
    monkeypatch.setitem(sys.modules, "azure", pkg)
    monkeypatch.setitem(sys.modules, "azure.communication", comm)
    monkeypatch.setitem(sys.modules, "azure.communication.email", mail)
    monkeypatch.setattr(settings, "ACS_CONNECTION_STRING", "endpoint=x")
    monkeypatch.setattr(settings, "ACS_SENDER_ADDRESS", "no-reply@x")
    mailer._send_acs("a@b.c", "Asunto", "<p>Hola</p>")
    assert mensajes[0]["recipients"]["to"][0]["address"] == "a@b.c"
    assert mensajes[0]["content"]["plainText"] == "Hola"


def test_plantillas_incluyen_enlace_con_token(monkeypatch):
    capturado = []
    monkeypatch.setattr(email_templates, "send_email", lambda to, subject, html: capturado.append((to, subject, html)))
    email_templates.send_verification_email("a@b.c", "TOK1")
    email_templates.send_password_reset_email("a@b.c", "TOK2")
    assert "http://frontend.test/verify-email?token=TOK1" in capturado[0][2]
    assert "http://frontend.test/reset-password?token=TOK2" in capturado[1][2]
