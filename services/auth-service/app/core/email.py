import resend

from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY


def send_verification_email(to_email: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    resend.Emails.send({
        "from": settings.RESEND_SENDER_EMAIL,
        "to": to_email,
        "subject": "Verifica tu cuenta en RADIA",
        "html": f"""
            <p>Hola,</p>
            <p>Confirma tu cuenta en RADIA haciendo clic en el siguiente enlace:</p>
            <p><a href="{link}">{link}</a></p>
            <p>Este enlace expira en 24 horas.</p>
        """,
    })


def send_password_reset_email(to_email: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    resend.Emails.send({
        "from": settings.RESEND_SENDER_EMAIL,
        "to": to_email,
        "subject": "Restablece tu contraseña en RADIA",
        "html": f"""
            <p>Hola,</p>
            <p>Solicitaste restablecer tu contraseña. Haz clic aquí:</p>
            <p><a href="{link}">{link}</a></p>
            <p>Si no fuiste tú, ignora este correo. Este enlace expira en 1 hora.</p>
        """,
    })
