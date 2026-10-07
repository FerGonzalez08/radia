"""Adaptador LangChain para modelos conversacionales configurables."""

import logging

from typing import Protocol

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from app.dominios.conversacion.mensajes import (
    RespuestaConversacion,
    SolicitudConversacion,
    TipoRespuestaConversacional,
)
from app.infraestructura.ia.errores import ProveedorIAIndisponibleError
from app.infraestructura.ia.esquemas_respuesta import RespuestaGeneradaControlada
from app.infraestructura.ia.prompts.orientacion_v1 import PROMPT_ORIENTACION_V1


registro = logging.getLogger(__name__)


class ModeloConversacionalLangChain(Protocol):
    """Interfaz mínima de un modelo invocable por LangChain."""

    def invoke(self, entrada: list[SystemMessage | HumanMessage]) -> object:
        """Genera una respuesta para los mensajes entregados."""


class AgenteConversacionalLangChain:
    """Adapta un modelo LangChain al puerto de conversación del proyecto."""

    def __init__(self, modelo: ModeloConversacionalLangChain, nombre_proveedor: str) -> None:
        self._modelo = modelo
        self.nombre_proveedor = nombre_proveedor

    def responder(self, solicitud: SolicitudConversacion) -> RespuestaConversacion:
        """Solicita una orientación y valida su estructura antes de entregarla."""
        contexto_diagnostico = (
            f"\nContexto orientativo disponible:\n{solicitud.contexto_diagnostico}"
            if solicitud.contexto_diagnostico
            else ""
        )
        contexto_documental = (
            f"\nEvidencia documental recuperada:\n{solicitud.contexto_documental}"
            if solicitud.contexto_documental
            else ""
        )
        mensajes = [
            SystemMessage(content=PROMPT_ORIENTACION_V1),
            HumanMessage(
                content=(
                    f"Consulta de la estudiante:\n{solicitud.mensaje}"
                    f"{contexto_diagnostico}{contexto_documental}"
                )
            ),
        ]
        try:
            resultado = self._modelo.invoke(mensajes)
        except Exception as error:
            registro.warning(
                "El proveedor de IA '%s' no pudo completar una solicitud.",
                self.nombre_proveedor,
            )
            raise ProveedorIAIndisponibleError(
                "El proveedor de IA no está disponible en este momento."
            ) from error
        contenido = getattr(resultado, "content", "")
        try:
            respuesta_controlada = RespuestaGeneradaControlada.model_validate_json(contenido)
        except (TypeError, ValidationError):
            registro.warning(
                "El proveedor de IA '%s' devolvió una respuesta fuera del formato controlado.",
                self.nombre_proveedor,
            )
            return RespuestaConversacion(
                respuesta=(
                    "No fue posible generar una orientación con información suficiente en este "
                    "momento. Puedes intentar nuevamente con una pregunta más específica."
                ),
                recursos=(),
                tipo_respuesta=TipoRespuestaConversacional.SIN_CONTEXTO_SUFICIENTE,
            )

        return RespuestaConversacion(
            respuesta=respuesta_controlada.respuesta,
            recursos=(),
            tipo_respuesta=TipoRespuestaConversacional(respuesta_controlada.tipo_respuesta),
        )
