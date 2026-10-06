from app.core.mailer import send_email


def send_mentorship_confirmation(
    to_email: str,
    counterpart_name: str,
    date: str,
    start_time: str,
    end_time: str,
) -> None:
    send_email(
        to_email,
        "Mentoría confirmada en RADIA",
        f"""
            <p>Hola,</p>
            <p>Tu mentoría con <strong>{counterpart_name}</strong> quedó confirmada.</p>
            <p><strong>Fecha:</strong> {date}<br>
            <strong>Hora:</strong> {start_time} - {end_time}</p>
            <p>Puedes coordinar por el chat de RADIA a partir de ahora.</p>
        """,
    )
