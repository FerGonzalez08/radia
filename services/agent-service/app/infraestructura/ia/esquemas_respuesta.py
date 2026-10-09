"""Esquemas Pydantic para validar las respuestas generadas por el proveedor."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RespuestaGeneradaControlada(BaseModel):
    """Formato mínimo permitido para la salida de un modelo conversacional."""

    tipo_respuesta: Literal["orientacion", "sin_contexto_suficiente"]
    respuesta: str = Field(min_length=1, max_length=1200)

    @field_validator("respuesta")
    @classmethod
    def validar_respuesta_con_contenido(cls, respuesta: str) -> str:
        """Evita que una respuesta formada solo por espacios se considere válida."""
        respuesta_limpia = respuesta.strip()
        if not respuesta_limpia:
            raise ValueError("La respuesta debe incluir contenido.")
        return respuesta_limpia
