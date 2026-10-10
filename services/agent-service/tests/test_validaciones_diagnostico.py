import pytest
from pydantic import ValidationError

from app.adaptadores.http.esquemas_diagnostico import SolicitudCrearDiagnostico
from tests.datos_diagnostico import crear_solicitud_valida


def test_acepta_solicitud_con_todas_las_respuestas_activas() -> None:
    """La validación acepta el instrumento y las seis preguntas simuladas."""
    solicitud = SolicitudCrearDiagnostico.model_validate(crear_solicitud_valida())

    assert solicitud.instrumento_id == "diagnostico-inicial-v1"
    assert len(solicitud.respuestas) == 6


def test_rechaza_preguntas_repetidas() -> None:
    """La validación rechaza respuestas duplicadas antes de persistirlas."""
    datos = crear_solicitud_valida()
    respuestas = datos["respuestas"]
    assert isinstance(respuestas, list)
    respuestas[-1] = {"pregunta_id": "TEC-001", "valor": 5}

    with pytest.raises(ValidationError, match="No se permiten preguntas repetidas"):
        SolicitudCrearDiagnostico.model_validate(datos)


def test_rechaza_instrumento_distinto_al_activo() -> None:
    """La validación no acepta versiones de instrumento no publicadas."""
    datos = crear_solicitud_valida()
    datos["instrumento_id"] = "instrumento-no-publicado"

    with pytest.raises(ValidationError, match="instrumento activo"):
        SolicitudCrearDiagnostico.model_validate(datos)
