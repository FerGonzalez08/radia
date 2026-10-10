from uuid import uuid4

from app.dominios.conversacion.mensajes import (
    SolicitudConversacion,
    TipoRespuestaConversacional,
)
from app.infraestructura.ia.agente_langchain import AgenteConversacionalLangChain


class ResultadoModeloFalso:
    """Resultado mínimo compatible con el adaptador LangChain."""

    def __init__(self, contenido: object) -> None:
        self.content = contenido


class ModeloConversacionalFalso:
    """Doble de prueba que devuelve el contenido configurado."""

    def __init__(self, contenido: object) -> None:
        self._contenido = contenido
        self.entrada: object | None = None

    def invoke(self, entrada: object) -> ResultadoModeloFalso:
        self.entrada = entrada
        return ResultadoModeloFalso(self._contenido)


def test_adaptador_acepta_una_respuesta_json_controlada() -> None:
    """Una respuesta con el formato acordado se convierte en salida de dominio."""
    modelo = ModeloConversacionalFalso(
        '{"tipo_respuesta":"orientacion","respuesta":"Practica con ejercicios pequeños."}'
    )
    agente = AgenteConversacionalLangChain(modelo, "falso")

    resultado = agente.responder(
        SolicitudConversacion(sesion_id=uuid4(), mensaje="¿Cómo practico programación?")
    )

    assert resultado.tipo_respuesta is TipoRespuestaConversacional.ORIENTACION
    assert resultado.respuesta == "Practica con ejercicios pequeños."


def test_adaptador_reemplaza_una_respuesta_no_json_por_una_salida_segura() -> None:
    """El texto libre del proveedor no se entrega directamente a la estudiante."""
    agente = AgenteConversacionalLangChain(ModeloConversacionalFalso("Texto no válido."), "falso")

    resultado = agente.responder(
        SolicitudConversacion(sesion_id=uuid4(), mensaje="¿Cómo practico programación?")
    )

    assert resultado.tipo_respuesta is TipoRespuestaConversacional.SIN_CONTEXTO_SUFICIENTE
    assert "No fue posible generar" in resultado.respuesta


def test_adaptador_entrega_la_evidencia_documental_al_modelo() -> None:
    """El modelo recibe solo el contexto documental construido por el caso de uso."""
    modelo = ModeloConversacionalFalso(
        '{"tipo_respuesta":"orientacion","respuesta":"Revisa la fuente indicada."}'
    )
    agente = AgenteConversacionalLangChain(modelo, "falso")

    agente.responder(
        SolicitudConversacion(
            sesion_id=uuid4(),
            mensaje="¿Qué plantea la fuente?",
            contexto_documental="[FCD-001.pdf, página 1] Contexto sobre brechas educativas.",
        )
    )

    assert modelo.entrada is not None
    assert "Evidencia documental recuperada" in str(modelo.entrada)
    assert "FCD-001.pdf" in str(modelo.entrada)
