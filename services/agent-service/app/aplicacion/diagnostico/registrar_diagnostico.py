from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from app.dominios.diagnostico.instrumento import INSTRUMENTO_ACTIVO, ids_preguntas_activas

if TYPE_CHECKING:
    from app.puertos.repositorio_diagnosticos import RepositorioDiagnosticos


@dataclass(frozen=True)
class RespuestaRegistroDiagnostico:
    """Respuesta validada que será persistida por el caso de uso."""

    pregunta_id: str
    valor: int


@dataclass(frozen=True)
class SolicitudRegistroDiagnostico:
    """Entrada independiente del transporte HTTP para registrar un diagnóstico."""

    instrumento_id: str
    respuestas: tuple[RespuestaRegistroDiagnostico, ...]


@dataclass(frozen=True)
class DiagnosticoRegistrado:
    """Resultado mínimo generado al registrar el diagnóstico."""

    id: UUID
    instrumento_id: str
    estado: str
    fecha_creacion: datetime


class RegistrarDiagnostico:
    """Registra un diagnóstico válido sin calcular perfiles ni recomendaciones."""

    def __init__(self, repositorio: "RepositorioDiagnosticos") -> None:
        self._repositorio = repositorio

    def ejecutar(self, solicitud: SolicitudRegistroDiagnostico) -> DiagnosticoRegistrado:
        """Valida las invariantes del instrumento antes de persistir el diagnóstico."""
        if solicitud.instrumento_id != INSTRUMENTO_ACTIVO.id:
            raise ValueError("El instrumento no corresponde al instrumento activo.")

        identificadores = [respuesta.pregunta_id for respuesta in solicitud.respuestas]
        if len(identificadores) != len(set(identificadores)):
            raise ValueError("No se permiten preguntas repetidas.")

        if set(identificadores) != ids_preguntas_activas():
            raise ValueError("El diagnóstico debe incluir todas y solo las preguntas activas.")

        if any(respuesta.valor < 1 or respuesta.valor > 5 for respuesta in solicitud.respuestas):
            raise ValueError("Cada respuesta debe estar entre 1 y 5.")

        return self._repositorio.guardar(solicitud)
