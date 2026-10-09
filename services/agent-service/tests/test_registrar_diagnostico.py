from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.aplicacion.diagnostico.registrar_diagnostico import (
    DiagnosticoRegistrado,
    RegistrarDiagnostico,
    RespuestaRegistroDiagnostico,
    SolicitudRegistroDiagnostico,
)
from app.dominios.diagnostico.instrumento import INSTRUMENTO_ACTIVO


class RepositorioDiagnosticosFalso:
    """Repositorio en memoria para probar reglas sin PostgreSQL."""

    def __init__(self) -> None:
        self.solicitudes_guardadas: list[SolicitudRegistroDiagnostico] = []

    def guardar(self, solicitud: SolicitudRegistroDiagnostico) -> DiagnosticoRegistrado:
        self.solicitudes_guardadas.append(solicitud)
        return DiagnosticoRegistrado(
            id=uuid4(),
            instrumento_id=solicitud.instrumento_id,
            estado="registrado",
            fecha_creacion=datetime.now(UTC),
        )


def crear_solicitud_valida() -> SolicitudRegistroDiagnostico:
    """Construye una entrada completa e independiente del transporte HTTP."""
    return SolicitudRegistroDiagnostico(
        instrumento_id=INSTRUMENTO_ACTIVO.id,
        respuestas=tuple(
            RespuestaRegistroDiagnostico(pregunta_id=pregunta.id, valor=4)
            for pregunta in INSTRUMENTO_ACTIVO.preguntas
        ),
    )


def test_registra_diagnostico_completo() -> None:
    """El caso de uso delega en el puerto solo después de validar la entrada."""
    repositorio = RepositorioDiagnosticosFalso()

    resultado = RegistrarDiagnostico(repositorio).ejecutar(crear_solicitud_valida())

    assert resultado.estado == "registrado"
    assert len(repositorio.solicitudes_guardadas) == 1


def test_no_persiste_diagnostico_con_preguntas_repetidas() -> None:
    """El caso de uso protege la persistencia ante una entrada inconsistente."""
    repositorio = RepositorioDiagnosticosFalso()
    solicitud = crear_solicitud_valida()
    respuestas = list(solicitud.respuestas)
    respuestas[-1] = RespuestaRegistroDiagnostico(pregunta_id="TEC-001", valor=4)
    solicitud_invalida = SolicitudRegistroDiagnostico(
        instrumento_id=solicitud.instrumento_id,
        respuestas=tuple(respuestas),
    )

    with pytest.raises(ValueError, match="preguntas repetidas"):
        RegistrarDiagnostico(repositorio).ejecutar(solicitud_invalida)

    assert repositorio.solicitudes_guardadas == []
