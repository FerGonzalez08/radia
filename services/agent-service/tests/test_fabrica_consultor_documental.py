"""Pruebas de activación segura del adaptador Gemini File Search."""

import pytest

from app.infraestructura.conocimiento.fabrica_consultor_documental import (
    crear_consultor_documental_opcional,
)
from app.infraestructura.ia.errores import ConfiguracionProveedorInvalidaError


def test_file_search_permanece_desactivado_por_defecto(monkeypatch: pytest.MonkeyPatch) -> None:
    """El flujo conversacional normal no requiere configurar File Search."""
    monkeypatch.delenv("USAR_FILE_SEARCH", raising=False)

    assert crear_consultor_documental_opcional() is None


def test_file_search_activo_exige_su_configuracion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Una activación incompleta falla antes de importar o invocar el proveedor."""
    monkeypatch.setenv("USAR_FILE_SEARCH", "true")
    monkeypatch.delenv("ALMACEN_FILE_SEARCH", raising=False)
    monkeypatch.delenv("MODELO_FILE_SEARCH", raising=False)
    monkeypatch.delenv("MODELO_IA", raising=False)
    monkeypatch.delenv("CLAVE_API_IA", raising=False)

    with pytest.raises(ConfiguracionProveedorInvalidaError, match="File Search requiere"):
        crear_consultor_documental_opcional()
