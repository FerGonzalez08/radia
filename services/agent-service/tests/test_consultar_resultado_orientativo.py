from uuid import uuid4

import pytest

from app.aplicacion.diagnostico.consultar_resultado_orientativo import (
    ConsultarResultadoOrientativo,
    DiagnosticoConRespuestas,
    DiagnosticoNoEncontradoError,
    RespuestaDiagnosticoRegistrada,
)


class RepositorioDiagnosticosConResultadoFalso:
    """Repositorio en memoria para aislar las reglas del caso de uso."""

    def __init__(self, diagnostico: DiagnosticoConRespuestas | None) -> None:
        self._diagnostico = diagnostico

    def obtener_por_id(self, diagnostico_id: object) -> DiagnosticoConRespuestas | None:
        return self._diagnostico


def crear_diagnostico() -> DiagnosticoConRespuestas:
    """Construye un diagnóstico completo con resultados de ambos grupos."""
    return DiagnosticoConRespuestas(
        id=uuid4(),
        instrumento_id="diagnostico-inicial-v1",
        estado="registrado",
        respuestas=(
            RespuestaDiagnosticoRegistrada("TEC-001", 5),
            RespuestaDiagnosticoRegistrada("TEC-002", 3),
            RespuestaDiagnosticoRegistrada("TEC-003", 4),
            RespuestaDiagnosticoRegistrada("ACT-001", 2),
            RespuestaDiagnosticoRegistrada("ACT-002", 4),
            RespuestaDiagnosticoRegistrada("ACT-003", 1),
        ),
    )


def test_calcula_fortalezas_y_oportunidades_desde_respuestas_persistidas() -> None:
    diagnostico = crear_diagnostico()
    caso_uso = ConsultarResultadoOrientativo(
        RepositorioDiagnosticosConResultadoFalso(diagnostico)
    )

    resultado = caso_uso.ejecutar(diagnostico.id)

    assert [item.pregunta_id for item in resultado.fortalezas] == [
        "TEC-001",
        "TEC-003",
        "ACT-002",
    ]
    assert [item.pregunta_id for item in resultado.oportunidades] == [
        "TEC-002",
        "ACT-001",
        "ACT-003",
    ]


def test_informa_cuando_el_diagnostico_no_existe() -> None:
    caso_uso = ConsultarResultadoOrientativo(
        RepositorioDiagnosticosConResultadoFalso(None)
    )

    with pytest.raises(DiagnosticoNoEncontradoError):
        caso_uso.ejecutar(uuid4())
