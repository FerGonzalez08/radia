"""Caso de uso para obtener la devolución orientativa de un diagnóstico."""

from dataclasses import dataclass
from uuid import UUID

from app.dominios.diagnostico.resultado_orientativo import (
    ClasificacionOrientativa,
    CompetenciaOrientativa,
    calcular_competencias_orientativas,
)
from app.puertos.repositorio_diagnosticos import RepositorioDiagnosticos


class DiagnosticoNoEncontradoError(Exception):
    """Indica que no existe un diagnóstico con el identificador solicitado."""


@dataclass(frozen=True)
class RespuestaDiagnosticoRegistrada:
    """Respuesta recuperada desde la persistencia para calcular el resultado."""

    pregunta_id: str
    valor: int


@dataclass(frozen=True)
class DiagnosticoConRespuestas:
    """Diagnóstico persistido y sus respuestas, sin datos personales."""

    id: UUID
    instrumento_id: str
    estado: str
    respuestas: tuple[RespuestaDiagnosticoRegistrada, ...]


@dataclass(frozen=True)
class ResultadoOrientativo:
    """Devolución calculada mediante reglas simuladas y explicables."""

    diagnostico_id: UUID
    instrumento_id: str
    fortalezas: tuple[CompetenciaOrientativa, ...]
    oportunidades: tuple[CompetenciaOrientativa, ...]


class ConsultarResultadoOrientativo:
    """Calcula una devolución desde el diagnóstico registrado solicitado."""

    def __init__(self, repositorio: RepositorioDiagnosticos) -> None:
        self._repositorio = repositorio

    def ejecutar(self, diagnostico_id: UUID) -> ResultadoOrientativo:
        """Obtiene las respuestas persistidas y aplica las reglas del dominio."""
        diagnostico = self._repositorio.obtener_por_id(diagnostico_id)
        if diagnostico is None:
            raise DiagnosticoNoEncontradoError

        competencias = calcular_competencias_orientativas(
            {
                respuesta.pregunta_id: respuesta.valor
                for respuesta in diagnostico.respuestas
            }
        )
        fortalezas = tuple(
            competencia
            for competencia in competencias
            if competencia.clasificacion == ClasificacionOrientativa.FORTALEZA
        )
        oportunidades = tuple(
            competencia
            for competencia in competencias
            if competencia.clasificacion == ClasificacionOrientativa.OPORTUNIDAD
        )
        return ResultadoOrientativo(
            diagnostico_id=diagnostico.id,
            instrumento_id=diagnostico.instrumento_id,
            fortalezas=fortalezas,
            oportunidades=oportunidades,
        )
