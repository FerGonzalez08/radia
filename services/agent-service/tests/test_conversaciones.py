from uuid import uuid4

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.aplicacion.conversacion.conversar_con_agente import ConversarConAgente
from app.dominios.conocimiento.documentos import (
    FragmentoDocumental,
    ResultadoConsultaDocumental,
)
from app.dominios.conversacion.mensajes import (
    RespuestaConversacion,
    SolicitudConversacion,
    TipoRespuestaConversacional,
)
from app.main import aplicacion


class AgenteConversacionalFalso:
    """Doble de prueba que evita cualquier llamada a proveedores externos."""

    def responder(self, solicitud: SolicitudConversacion) -> RespuestaConversacion:
        return RespuestaConversacion(respuesta=f"Orientación para: {solicitud.mensaje}", recursos=())


class AgenteConversacionalContable:
    """Doble de prueba que permite verificar si se consulta el proveedor."""

    def __init__(self) -> None:
        self.llamadas = 0

    def responder(self, solicitud: SolicitudConversacion) -> RespuestaConversacion:
        self.llamadas += 1
        return RespuestaConversacion(respuesta="Respuesta del proveedor.", recursos=())


class ConsultorDocumentalFalso:
    """Doble de prueba para controlar la evidencia recuperada."""

    def __init__(self, fragmentos: tuple[FragmentoDocumental, ...]) -> None:
        self.fragmentos = fragmentos
        self.llamadas = 0

    def consultar(self, _consulta: object) -> ResultadoConsultaDocumental:
        self.llamadas += 1
        return ResultadoConsultaDocumental(fragmentos=self.fragmentos)


class ConsultorDocumentalConRespuestaFalsa(ConsultorDocumentalFalso):
    """Simula la respuesta estructurada generada en la misma consulta documental."""

    def consultar(self, _consulta: object) -> ResultadoConsultaDocumental:
        self.llamadas += 1
        return ResultadoConsultaDocumental(
            fragmentos=self.fragmentos,
            respuesta_orientativa="Orientación sustentada por la fuente.",
            tipo_respuesta="orientacion",
        )


def test_caso_de_uso_delega_el_mensaje_al_puerto() -> None:
    """El caso de uso devuelve la respuesta entregada por el puerto."""
    solicitud = SolicitudConversacion(sesion_id=uuid4(), mensaje="Quiero practicar programación.")

    resultado = ConversarConAgente(AgenteConversacionalFalso()).ejecutar(solicitud)

    assert resultado.respuesta == "Orientación para: Quiero practicar programación."
    assert "No corresponde a una evaluación" in resultado.aviso_alcance


def test_endpoint_responde_con_el_proveedor_simulado(monkeypatch: MonkeyPatch) -> None:
    """La ruta funciona sin claves ni peticiones a un modelo externo."""
    monkeypatch.setenv("PROVEEDOR_IA", "simulado")
    monkeypatch.setenv("USAR_FILE_SEARCH", "false")
    cliente = TestClient(aplicacion)

    respuesta = cliente.post(
        "/api/v1/conversaciones",
        json={"sesion_id": str(uuid4()), "mensaje": "Necesito ayuda con programación."},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["proveedor_modelo"] == "simulado"
    assert len(cuerpo["recursos"]) == 1
    assert "No corresponde a una evaluación" in cuerpo["aviso_alcance"]


def test_endpoint_rechaza_un_mensaje_vacio() -> None:
    """Pydantic bloquea solicitudes inválidas antes de invocar el agente."""
    cliente = TestClient(aplicacion)

    respuesta = cliente.post(
        "/api/v1/conversaciones",
        json={"sesion_id": str(uuid4()), "mensaje": ""},
    )

    assert respuesta.status_code == 422


def test_caso_de_uso_bloquea_datos_sensibles_sin_consultar_al_proveedor() -> None:
    """Las reglas protegen datos antes de delegar al adaptador externo."""
    agente = AgenteConversacionalContable()
    solicitud = SolicitudConversacion(
        sesion_id=uuid4(),
        mensaje="¿Puedo enviarte mi contraseña para que revises mi cuenta?",
    )

    resultado = ConversarConAgente(agente).ejecutar(solicitud)

    assert agente.llamadas == 0
    assert "no compartas contraseñas" in resultado.respuesta
    assert resultado.tipo_respuesta is TipoRespuestaConversacional.FUERA_DE_ALCANCE


def test_caso_de_uso_bloquea_evaluaciones_no_permitidas() -> None:
    """El agente no delega evaluaciones psicológicas al proveedor de IA."""
    agente = AgenteConversacionalContable()
    solicitud = SolicitudConversacion(
        sesion_id=uuid4(),
        mensaje="Necesito un diagnóstico psicológico sobre mi desempeño.",
    )

    resultado = ConversarConAgente(agente).ejecutar(solicitud)

    assert agente.llamadas == 0
    assert "No realizo evaluaciones psicológicas" in resultado.respuesta
    assert resultado.tipo_respuesta is TipoRespuestaConversacional.FUERA_DE_ALCANCE


def test_caso_de_uso_bloquea_evaluaciones_antes_de_consultar_file_search() -> None:
    """Las reglas de alcance se aplican antes de recuperar fuentes externas."""
    agente = AgenteConversacionalContable()
    consultor = ConsultorDocumentalFalso(())
    solicitud = SolicitudConversacion(
        sesion_id=uuid4(),
        mensaje="Necesito un diagnóstico psicológico sobre mi desempeño.",
    )

    resultado = ConversarConAgente(agente, consultor).ejecutar(solicitud)

    assert consultor.llamadas == 0
    assert agente.llamadas == 0
    assert resultado.tipo_respuesta is TipoRespuestaConversacional.FUERA_DE_ALCANCE


def test_caso_de_uso_bloquea_consultas_fuera_del_alcance() -> None:
    """Las consultas ajenas al objetivo del MVP no llegan al proveedor."""
    agente = AgenteConversacionalContable()
    solicitud = SolicitudConversacion(
        sesion_id=uuid4(),
        mensaje="¿Cuál es el pronóstico del clima para mañana?",
    )

    resultado = ConversarConAgente(agente).ejecutar(solicitud)

    assert agente.llamadas == 0
    assert "fuera del alcance" in resultado.respuesta
    assert resultado.tipo_respuesta is TipoRespuestaConversacional.FUERA_DE_ALCANCE


def test_caso_de_uso_delega_consultas_de_aprendizaje_permitidas() -> None:
    """Las consultas académicas válidas conservan el flujo hacia el proveedor."""
    agente = AgenteConversacionalContable()
    solicitud = SolicitudConversacion(
        sesion_id=uuid4(),
        mensaje="¿Cómo puedo practicar fundamentos de programación?",
    )

    resultado = ConversarConAgente(agente).ejecutar(solicitud)

    assert agente.llamadas == 1
    assert resultado.respuesta == "Respuesta del proveedor."


def test_caso_de_uso_agrega_contexto_y_fuentes_documentales() -> None:
    """La evidencia recuperada llega al agente y sus citas llegan a la respuesta."""
    agente = AgenteConversacionalFalso()
    consultor = ConsultorDocumentalFalso(
        (
            FragmentoDocumental(
                contenido="La fuente aporta contexto sobre brechas educativas.",
                fuente_id="FCD-001.pdf",
                referencia="fuentes/FCD-001",
                ubicacion="página 1",
            ),
        )
    )
    solicitud = SolicitudConversacion(
        sesion_id=uuid4(), mensaje="¿Qué dice la fuente sobre las brechas?"
    )

    resultado = ConversarConAgente(agente, consultor).ejecutar(solicitud)

    assert consultor.llamadas == 1
    assert resultado.fuentes_documentales[0].identificador == "FCD-001.pdf"
    assert resultado.fuentes_documentales[0].ubicacion == "página 1"


def test_caso_de_uso_reutiliza_respuesta_de_file_search_sin_segunda_llamada() -> None:
    """Una respuesta JSON documental evita invocar por segunda vez al agente."""
    agente = AgenteConversacionalContable()
    consultor = ConsultorDocumentalConRespuestaFalsa(
        (
            FragmentoDocumental(
                contenido="La fuente aporta contexto sobre brechas educativas.",
                fuente_id="FCD-001.pdf",
                referencia="fuentes/FCD-001",
                ubicacion="página 1",
            ),
        )
    )
    solicitud = SolicitudConversacion(
        sesion_id=uuid4(), mensaje="¿Qué dice la fuente sobre las brechas?"
    )

    resultado = ConversarConAgente(agente, consultor).ejecutar(solicitud)

    assert consultor.llamadas == 1
    assert agente.llamadas == 0
    assert resultado.respuesta == "Orientación sustentada por la fuente."


def test_caso_de_uso_no_delega_si_file_search_no_recupera_evidencia() -> None:
    """La respuesta se limita cuando File Search no encuentra una fuente aprobada."""
    agente = AgenteConversacionalContable()
    consultor = ConsultorDocumentalFalso(())
    solicitud = SolicitudConversacion(
        sesion_id=uuid4(), mensaje="Necesito orientación sobre una fuente documental."
    )

    resultado = ConversarConAgente(agente, consultor).ejecutar(solicitud)

    assert consultor.llamadas == 1
    assert agente.llamadas == 0
    assert resultado.tipo_respuesta is TipoRespuestaConversacional.SIN_CONTEXTO_SUFICIENTE
