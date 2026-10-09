"""Adaptador de Gemini File Search para el puerto documental."""

import os
import logging
import time
from typing import Protocol

from app.dominios.conocimiento.documentos import (
    ConsultaDocumental,
    FragmentoDocumental,
    ResultadoConsultaDocumental,
)
from app.puertos.consultor_documental import ConsultorDocumental
from app.infraestructura.ia.esquemas_respuesta import RespuestaGeneradaControlada
from app.infraestructura.ia.prompts.orientacion_v1 import PROMPT_ORIENTACION_V1


registro = logging.getLogger(__name__)


class InteraccionesGemini(Protocol):
    """Parte mínima del cliente Gemini usada para recuperar evidencia."""

    def create(self, **parametros: object) -> object:
        """Crea una interacción usando las herramientas configuradas."""


class ClienteGemini(Protocol):
    """Cliente mínimo para desacoplar las pruebas del SDK externo."""

    interactions: InteraccionesGemini


class ConsultorDocumentalGemini(ConsultorDocumental):
    """Recupera evidencia trazable desde un almacén de Gemini File Search."""

    def __init__(self, cliente: ClienteGemini, almacen: str, modelo: str) -> None:
        self._cliente = cliente
        self._almacen = almacen
        self._modelo = modelo

    def consultar(self, consulta: ConsultaDocumental) -> ResultadoConsultaDocumental:
        """Consulta el almacén configurado y conserva solo citas de archivos."""
        if not consulta.pregunta.strip():
            return ResultadoConsultaDocumental()

        inicio = time.perf_counter()
        interaccion = self._cliente.interactions.create(
            model=self._modelo,
            input=_construir_entrada_controlada(consulta.pregunta),
            tools=[
                {
                    "type": "file_search",
                    "file_search_store_names": [self._almacen],
                }
            ],
        )
        duracion_ms = round((time.perf_counter() - inicio) * 1000)
        registro.info("File Search y validación de respuesta completados en %s ms.", duracion_ms)
        fragmentos = tuple(_extraer_fragmentos_citados(interaccion))
        respuesta_controlada = _extraer_respuesta_controlada(interaccion)
        return ResultadoConsultaDocumental(
            fragmentos=fragmentos,
            respuesta_orientativa=(
                respuesta_controlada.respuesta if respuesta_controlada else None
            ),
            tipo_respuesta=(
                respuesta_controlada.tipo_respuesta if respuesta_controlada else None
            ),
        )


def crear_consultor_documental_desde_entorno() -> ConsultorDocumentalGemini:
    """Construye el adaptador sin exponer la clave en otras capas."""
    clave_api = os.getenv("CLAVE_API_IA", "").strip()
    almacen = os.getenv("ALMACEN_FILE_SEARCH", "").strip()
    modelo = os.getenv("MODELO_FILE_SEARCH", "").strip() or os.getenv("MODELO_IA", "").strip()
    if not clave_api or not almacen or not modelo:
        raise ValueError(
            "File Search requiere CLAVE_API_IA, ALMACEN_FILE_SEARCH y MODELO_FILE_SEARCH "
            "o MODELO_IA."
        )

    from google import genai

    return ConsultorDocumentalGemini(
        cliente=genai.Client(api_key=clave_api),
        almacen=almacen,
        modelo=modelo,
    )


def _extraer_fragmentos_citados(interaccion: object) -> list[FragmentoDocumental]:
    """Convierte las citas de Gemini en objetos simples del dominio."""
    fragmentos: list[FragmentoDocumental] = []
    for paso in getattr(interaccion, "steps", ()) or ():
        if getattr(paso, "type", None) != "model_output":
            continue
        for bloque in getattr(paso, "content", ()) or ():
            if getattr(bloque, "type", None) != "text":
                continue
            contenido = str(getattr(bloque, "text", "")).strip()
            if not contenido:
                continue
            for cita in getattr(bloque, "annotations", ()) or ():
                if getattr(cita, "type", None) != "file_citation":
                    continue
                nombre_archivo = str(getattr(cita, "file_name", "fuente_documental"))
                referencia = str(
                    getattr(cita, "document_uri", None) or nombre_archivo
                )
                pagina = getattr(cita, "page_number", None)
                fragmentos.append(
                    FragmentoDocumental(
                        contenido=contenido,
                        fuente_id=nombre_archivo,
                        referencia=referencia,
                        ubicacion=f"página {pagina}" if pagina is not None else None,
                    )
                )
    return fragmentos


def _construir_entrada_controlada(pregunta: str) -> str:
    """Envía reglas y pregunta en una sola interacción con File Search."""
    reglas_sin_formato = PROMPT_ORIENTACION_V1.split("\n\nFormato obligatorio:", maxsplit=1)[0]
    return (
        f"{reglas_sin_formato}\n\n"
        "Responde con orientación breve en texto plano. Usa solamente la evidencia "
        "recuperada por File Search.\n\n"
        f"Consulta de la estudiante:\n{pregunta}"
    )


def _extraer_respuesta_controlada(
    interaccion: object,
) -> RespuestaGeneradaControlada | None:
    """Valida la salida JSON sin volver a llamar al modelo conversacional."""
    texto_salida = str(getattr(interaccion, "output_text", "")).strip()
    if not texto_salida:
        return None
    try:
        return RespuestaGeneradaControlada.model_validate(
            {"tipo_respuesta": "orientacion", "respuesta": texto_salida}
        )
    except ValueError:
        registro.warning("File Search devolvió una respuesta fuera del formato controlado.")
        return None
