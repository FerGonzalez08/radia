from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.adaptadores.http.dependencias import obtener_repositorio_diagnosticos
from app.aplicacion.diagnostico.registrar_diagnostico import DiagnosticoRegistrado
from app.aplicacion.diagnostico.consultar_resultado_orientativo import (
    DiagnosticoConRespuestas,
    RespuestaDiagnosticoRegistrada,
)
from app.main import aplicacion
from tests.datos_diagnostico import crear_solicitud_valida


class RepositorioDiagnosticosMemoria:
    """Repositorio aislado para probar el contrato HTTP sin base de datos."""

    def __init__(self) -> None:
        self.cantidad_guardada = 0

    def guardar(self, solicitud: object) -> DiagnosticoRegistrado:
        self.cantidad_guardada += 1
        return DiagnosticoRegistrado(
            id=uuid4(),
            instrumento_id="diagnostico-inicial-v1",
            estado="registrado",
            fecha_creacion=datetime.now(UTC),
        )

    def obtener_por_id(self, diagnostico_id: object) -> DiagnosticoConRespuestas | None:
        if self.cantidad_guardada == 0:
            return None
        return DiagnosticoConRespuestas(
            id=diagnostico_id,
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


def crear_cliente(repositorio: RepositorioDiagnosticosMemoria) -> TestClient:
    """Crea un cliente con el puerto de persistencia reemplazado."""
    aplicacion.dependency_overrides[obtener_repositorio_diagnosticos] = lambda: repositorio
    return TestClient(aplicacion)


def test_consulta_instrumento_activo() -> None:
    """El endpoint expone seis preguntas simuladas con escala de uno a cinco."""
    cliente = TestClient(aplicacion)

    respuesta = cliente.get("/api/v1/diagnosticos/instrumento-activo")

    assert respuesta.status_code == 200
    assert respuesta.json()["instrumento_id"] == "diagnostico-inicial-v1"
    assert len(respuesta.json()["preguntas"]) == 6


def test_registra_diagnostico_valido() -> None:
    """El endpoint devuelve 201 al recibir el instrumento completo."""
    repositorio = RepositorioDiagnosticosMemoria()
    cliente = crear_cliente(repositorio)

    respuesta = cliente.post("/api/v1/diagnosticos", json=crear_solicitud_valida())

    aplicacion.dependency_overrides.clear()
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "registrado"
    assert repositorio.cantidad_guardada == 1


def test_rechaza_diagnostico_incompleto_sin_persistir() -> None:
    """El endpoint devuelve 422 y no guarda una solicitud con preguntas faltantes."""
    repositorio = RepositorioDiagnosticosMemoria()
    cliente = crear_cliente(repositorio)
    datos = crear_solicitud_valida()
    datos["respuestas"] = datos["respuestas"][:2]

    respuesta = cliente.post("/api/v1/diagnosticos", json=datos)

    aplicacion.dependency_overrides.clear()
    assert respuesta.status_code == 422
    assert repositorio.cantidad_guardada == 0


def test_consulta_resultado_orientativo_de_diagnostico_registrado() -> None:
    """El endpoint entrega la división calculada por el backend."""
    repositorio = RepositorioDiagnosticosMemoria()
    cliente = crear_cliente(repositorio)
    diagnostico_id = uuid4()
    repositorio.cantidad_guardada = 1

    respuesta = cliente.get(
        f"/api/v1/diagnosticos/{diagnostico_id}/resultado-orientativo"
    )

    aplicacion.dependency_overrides.clear()
    assert respuesta.status_code == 200
    assert len(respuesta.json()["fortalezas"]) == 3
    assert len(respuesta.json()["oportunidades"]) == 3
    assert "reglas simuladas" in respuesta.json()["aviso"]


def test_informa_cuando_no_existe_resultado_para_el_identificador() -> None:
    """El endpoint no revela resultados inexistentes."""
    repositorio = RepositorioDiagnosticosMemoria()
    cliente = crear_cliente(repositorio)

    respuesta = cliente.get(
        f"/api/v1/diagnosticos/{uuid4()}/resultado-orientativo"
    )

    aplicacion.dependency_overrides.clear()
    assert respuesta.status_code == 404
