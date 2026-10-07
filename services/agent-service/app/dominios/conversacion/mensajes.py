"""Objetos de valor para una interacción conversacional del MVP."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


AVISO_ALCANCE_ORIENTACION = (
    "Esta conversación ofrece orientación general para el aprendizaje. "
    "No corresponde a una evaluación académica, psicológica ni profesional."
)


class TipoRespuestaConversacional(StrEnum):
    """Tipos controlados que puede devolver el agente conversacional."""

    ORIENTACION = "orientacion"
    FUERA_DE_ALCANCE = "fuera_de_alcance"
    SIN_CONTEXTO_SUFICIENTE = "sin_contexto_suficiente"


@dataclass(frozen=True)
class SolicitudConversacion:
    """Mensaje y contexto mínimo entregados al agente conversacional."""

    sesion_id: UUID
    mensaje: str
    diagnostico_id: UUID | None = None
    contexto_diagnostico: str | None = None
    contexto_documental: str | None = None


@dataclass(frozen=True)
class RecursoConversacional:
    """Recurso simulado que el agente puede referenciar en su respuesta."""

    titulo: str
    descripcion: str
    enlace: str | None = None


@dataclass(frozen=True)
class FuenteDocumentalConsultada:
    """Referencia breve de una fuente usada para orientar la respuesta."""

    identificador: str
    referencia: str
    ubicacion: str | None = None


@dataclass(frozen=True)
class RespuestaConversacion:
    """Salida segura y estructurada de una conversación orientativa."""

    respuesta: str
    recursos: tuple[RecursoConversacional, ...]
    fuentes_documentales: tuple[FuenteDocumentalConsultada, ...] = ()
    tipo_respuesta: TipoRespuestaConversacional = TipoRespuestaConversacional.ORIENTACION
    aviso_alcance: str = AVISO_ALCANCE_ORIENTACION
