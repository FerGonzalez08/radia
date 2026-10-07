from dataclasses import dataclass


@dataclass(frozen=True)
class PreguntaInstrumento:
    """Pregunta fija del instrumento simulado del MVP."""

    id: str
    texto: str
    categoria: str


@dataclass(frozen=True)
class InstrumentoDiagnostico:
    """Instrumento publicado para la primera iteración del MVP."""

    id: str
    nombre: str
    descripcion: str
    preguntas: tuple[PreguntaInstrumento, ...]


INSTRUMENTO_ACTIVO = InstrumentoDiagnostico(
    id="diagnostico-inicial-v1",
    nombre="Instrumento simulado de diagnóstico inicial",
    descripcion=(
        "Instrumento simulado para validar el flujo técnico del MVP. "
        "No corresponde a una encuesta oficial del semillero Kerberos."
    ),
    preguntas=(
        PreguntaInstrumento(
            id="TEC-001",
            texto="¿Qué tan segura te sientes al resolver problemas de programación paso a paso?",
            categoria="tecnica",
        ),
        PreguntaInstrumento(
            id="TEC-002",
            texto="¿Qué tan segura te sientes al interpretar datos básicos de una aplicación?",
            categoria="tecnica",
        ),
        PreguntaInstrumento(
            id="TEC-003",
            texto="¿Qué tan segura te sientes al usar conceptos básicos de bases de datos?",
            categoria="tecnica",
        ),
        PreguntaInstrumento(
            id="ACT-001",
            texto="¿Qué tan segura te sientes al pedir apoyo cuando enfrentas una dificultad académica?",
            categoria="actitudinal",
        ),
        PreguntaInstrumento(
            id="ACT-002",
            texto="¿Qué tan capaz te sientes de continuar aprendiendo ante un error técnico?",
            categoria="actitudinal",
        ),
        PreguntaInstrumento(
            id="ACT-003",
            texto="¿Qué tan segura te sientes al comunicar tus ideas técnicas a otras personas?",
            categoria="actitudinal",
        ),
    ),
)


def obtener_instrumento_activo() -> InstrumentoDiagnostico:
    """Obtiene el instrumento fijo disponible durante esta iteración."""
    return INSTRUMENTO_ACTIVO


def ids_preguntas_activas() -> set[str]:
    """Entrega los identificadores válidos del instrumento activo."""
    return {pregunta.id for pregunta in INSTRUMENTO_ACTIVO.preguntas}
