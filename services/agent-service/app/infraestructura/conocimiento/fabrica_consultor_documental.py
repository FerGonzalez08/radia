"""Construcción opcional del consultor documental desde variables de entorno."""

import os

from app.infraestructura.conocimiento.gemini_file_search import (
    ConsultorDocumentalGemini,
    crear_consultor_documental_desde_entorno,
)
from app.infraestructura.ia.errores import ConfiguracionProveedorInvalidaError


def crear_consultor_documental_opcional() -> ConsultorDocumentalGemini | None:
    """Activa File Search solo cuando se configura explícitamente en el entorno."""
    usar_file_search = os.getenv("USAR_FILE_SEARCH", "false").strip().lower()
    if usar_file_search not in {"true", "1", "si"}:
        return None
    try:
        return crear_consultor_documental_desde_entorno()
    except ValueError as error:
        raise ConfiguracionProveedorInvalidaError(str(error)) from error
