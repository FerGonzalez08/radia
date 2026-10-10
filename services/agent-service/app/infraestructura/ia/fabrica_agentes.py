"""Construcción del proveedor conversacional a partir de variables de entorno."""

import os

from app.infraestructura.ia.agente_langchain import AgenteConversacionalLangChain
from app.infraestructura.ia.agente_simulado import AgenteConversacionalSimulado
from app.infraestructura.ia.errores import ConfiguracionProveedorInvalidaError
from app.puertos.agente_conversacional import AgenteConversacional


def obtener_proveedor_activo() -> str:
    """Devuelve el proveedor solicitado, usando el simulador por defecto."""
    return os.getenv("PROVEEDOR_IA", "simulado").strip().lower() or "simulado"


def crear_agente_conversacional() -> AgenteConversacional:
    """Crea el adaptador sin exponer credenciales a las capas internas."""
    proveedor = obtener_proveedor_activo()
    if proveedor == "simulado":
        return AgenteConversacionalSimulado()

    clave_api = os.getenv("CLAVE_API_IA", "").strip()
    modelo = os.getenv("MODELO_IA", "").strip()
    if not clave_api or not modelo:
        raise ConfiguracionProveedorInvalidaError(
            "El proveedor configurado requiere CLAVE_API_IA y MODELO_IA."
        )

    try:
        temperatura = float(os.getenv("TEMPERATURA_IA", "0.2"))
    except ValueError as error:
        raise ConfiguracionProveedorInvalidaError(
            "TEMPERATURA_IA debe ser un valor numérico."
        ) from error
    if proveedor == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        cliente = ChatGoogleGenerativeAI(
            model=modelo,
            google_api_key=clave_api,
            temperature=temperatura,
            max_retries=0,
        )
        return AgenteConversacionalLangChain(cliente, proveedor)

    if proveedor in {"openai", "openrouter"}:
        from langchain_openai import ChatOpenAI

        url_base = os.getenv("URL_BASE_IA", "").strip()
        if proveedor == "openrouter" and not url_base:
            url_base = "https://openrouter.ai/api/v1"
        cliente = ChatOpenAI(
            model=modelo,
            api_key=clave_api,
            base_url=url_base or None,
            temperature=temperatura,
            max_retries=0,
        )
        return AgenteConversacionalLangChain(cliente, proveedor)

    raise ConfiguracionProveedorInvalidaError(
        "PROVEEDOR_IA debe ser simulado, gemini, openai u openrouter."
    )
