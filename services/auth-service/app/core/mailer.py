"""Envío de correo con selección de proveedor.

EMAIL_PROVIDER=resend (por defecto, desarrollo local) o EMAIL_PROVIDER=acs (Azure Communication Services).
Solo este módulo conoce a los proveedores: el resto del servicio llama a send_email().
"""
import logging
import re

from app.core.config import settings

logger = logging.getLogger(__name__)


def _plain_text(html: str) -> str:
    text = re.sub(r"<br\s*/?>|</p>", "\n", html)
    text = re.sub(r"<[^>]+>", "", text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _send_resend(to_email: str, subject: str, html: str) -> None:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        "from": settings.RESEND_SENDER_EMAIL,
        "to": to_email,
        "subject": subject,
        "html": html,
    })


def _send_acs(to_email: str, subject: str, html: str) -> None:
    if not settings.ACS_CONNECTION_STRING or not settings.ACS_SENDER_ADDRESS:
        raise RuntimeError("EMAIL_PROVIDER=acs requiere ACS_CONNECTION_STRING y ACS_SENDER_ADDRESS")

    from azure.communication.email import EmailClient

    client = EmailClient.from_connection_string(settings.ACS_CONNECTION_STRING)
    # No se espera el resultado del envío: no debe bloquear la petición del usuario.
    client.begin_send({
        "senderAddress": settings.ACS_SENDER_ADDRESS,
        "recipients": {"to": [{"address": to_email}]},
        "content": {"subject": subject, "plainText": _plain_text(html), "html": html},
    })


def send_email(to_email: str, subject: str, html: str) -> None:
    """Envía un correo por el proveedor configurado.

    Si falla, deja el error en el log (sin la dirección del destinatario) y lo vuelve a lanzar;
    cada endpoint decide si el fallo del correo debe o no afectar su respuesta.
    """
    try:
        if settings.EMAIL_PROVIDER == "acs":
            _send_acs(to_email, subject, html)
        else:
            _send_resend(to_email, subject, html)
    except Exception:
        logger.exception("No se pudo enviar un correo (proveedor: %s)", settings.EMAIL_PROVIDER)
        raise
