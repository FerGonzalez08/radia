from app.dominios.diagnostico.instrumento import INSTRUMENTO_ACTIVO


def crear_respuestas_validas() -> list[dict[str, int | str]]:
    """Crea respuestas completas para el instrumento simulado."""
    return [
        {"pregunta_id": pregunta.id, "valor": 4}
        for pregunta in INSTRUMENTO_ACTIVO.preguntas
    ]


def crear_solicitud_valida() -> dict[str, object]:
    """Crea un cuerpo JSON válido para el endpoint de diagnóstico."""
    return {
        "instrumento_id": INSTRUMENTO_ACTIVO.id,
        "respuestas": crear_respuestas_validas(),
    }
