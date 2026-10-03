import resend

from app.core.config import settings

resend.api_key = settings.RESEND_API_KEY


def send_mentorship_confirmation(
    to_email: str,
    counterpart_name: str,
    date: str,
    start_time: str,
    end_time: str,
) -> None:
    resend.Emails.send({
        "from": settings.RESEND_SENDER_EMAIL,
        "to": to_email,
        "subject": "Mentoría confirmada en RADIA",
        "html": f"""
            <p>Hola,</p>
            <p>Tu mentoría con <strong>{counterpart_name}</strong> quedó confirmada.</p>
            <p><strong>Fecha:</strong> {date}<br>
            <strong>Hora:</strong> {start_time} - {end_time}</p>
            <p>Puedes coordinar por el chat de RADIA a partir de ahora.</p>
        """,
    })
