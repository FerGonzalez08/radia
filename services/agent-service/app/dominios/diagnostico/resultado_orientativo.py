"""Reglas deterministas del resultado orientativo del diagnóstico simulado."""

from dataclasses import dataclass
from enum import StrEnum


class ClasificacionOrientativa(StrEnum):
    """Clasificaciones informativas, sin carácter de evaluación académica."""

    FORTALEZA = "fortaleza"
    OPORTUNIDAD = "oportunidad"


@dataclass(frozen=True)
class DefinicionCompetencia:
    """Relación entre una pregunta del instrumento y una competencia observable."""

    pregunta_id: str
    nombre: str
    categoria: str
    recurso_simulado: str


@dataclass(frozen=True)
class CompetenciaOrientativa:
    """Resultado explicable de una respuesta del instrumento simulado."""

    pregunta_id: str
    nombre: str
    categoria: str
    puntaje: int
    clasificacion: ClasificacionOrientativa
    recurso_simulado: str


COMPETENCIAS_ORIENTATIVAS = (
    DefinicionCompetencia(
        pregunta_id="TEC-001",
        nombre="Resolución de problemas de programación",
        categoria="tecnica",
        recurso_simulado="Guía simulada: descomposición de problemas de programación.",
    ),
    DefinicionCompetencia(
        pregunta_id="TEC-002",
        nombre="Interpretación básica de datos",
        categoria="tecnica",
        recurso_simulado="Recurso simulado: práctica de lectura e interpretación de datos.",
    ),
    DefinicionCompetencia(
        pregunta_id="TEC-003",
        nombre="Fundamentos de bases de datos",
        categoria="tecnica",
        recurso_simulado="Recurso simulado: repaso de conceptos básicos de bases de datos.",
    ),
    DefinicionCompetencia(
        pregunta_id="ACT-001",
        nombre="Búsqueda de apoyo ante dificultades académicas",
        categoria="actitudinal",
        recurso_simulado="Recurso simulado: estrategias para solicitar apoyo académico.",
    ),
    DefinicionCompetencia(
        pregunta_id="ACT-002",
        nombre="Persistencia ante el aprendizaje técnico",
        categoria="actitudinal",
        recurso_simulado="Recurso simulado: estrategias de aprendizaje ante el error.",
    ),
    DefinicionCompetencia(
        pregunta_id="ACT-003",
        nombre="Comunicación de ideas técnicas",
        categoria="actitudinal",
        recurso_simulado="Recurso simulado: práctica de comunicación de ideas técnicas.",
    ),
)


def calcular_competencias_orientativas(
    respuestas_por_pregunta: dict[str, int],
) -> tuple[CompetenciaOrientativa, ...]:
    """Clasifica respuestas completas con una regla fija y verificable.

    Los puntajes 4 y 5 se presentan como fortalezas; los puntajes 1 a 3,
    como oportunidades de fortalecimiento. Esta regla es solo demostrativa
    para el MVP y no sustituye una evaluación académica o psicológica.
    """
    competencias = []
    for definicion in COMPETENCIAS_ORIENTATIVAS:
        puntaje = respuestas_por_pregunta[definicion.pregunta_id]
        clasificacion = (
            ClasificacionOrientativa.FORTALEZA
            if puntaje >= 4
            else ClasificacionOrientativa.OPORTUNIDAD
        )
        competencias.append(
            CompetenciaOrientativa(
                pregunta_id=definicion.pregunta_id,
                nombre=definicion.nombre,
                categoria=definicion.categoria,
                puntaje=puntaje,
                clasificacion=clasificacion,
                recurso_simulado=definicion.recurso_simulado,
            )
        )
    return tuple(competencias)
