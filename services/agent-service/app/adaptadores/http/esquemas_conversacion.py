"""Contratos HTTP del módulo de conversación."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SolicitudConversacionEntrada(BaseModel):
    """Contrato para enviar un mensaje al agente del MVP."""

    sesion_id: UUID
    mensaje: str = Field(min_length=1, max_length=1000)
    diagnostico_id: UUID | None = None

    @field_validator("mensaje")
    @classmethod
    def validar_mensaje_con_contenido(cls, mensaje: str) -> str:
        """Evita que una cadena formada solo por espacios llegue al proveedor."""
        mensaje_limpio = mensaje.strip()
        if not mensaje_limpio:
            raise ValueError("El mensaje debe incluir contenido.")
        return mensaje_limpio


class RecursoConversacionRespuesta(BaseModel):
    """Recurso que se muestra junto con la orientación."""

    titulo: str
    descripcion: str
    enlace: str | None = None


class FuenteDocumentalRespuesta(BaseModel):
    """Referencia de una fuente documental consultada para la orientación."""

    identificador: str
    referencia: str
    ubicacion: str | None = None


class RespuestaConversacionSalida(BaseModel):
    """Contrato de salida de una respuesta conversacional."""

    tipo_respuesta: Literal[
        "orientacion", "fuera_de_alcance", "sin_contexto_suficiente"
    ]
    respuesta: str
    recursos: list[RecursoConversacionRespuesta]
    fuentes_documentales: list[FuenteDocumentalRespuesta]
    aviso_alcance: str
    proveedor_modelo: str
