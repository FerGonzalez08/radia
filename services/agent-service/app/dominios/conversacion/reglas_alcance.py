"""Reglas deterministas que limitan el alcance del agente conversacional."""

from dataclasses import dataclass
from enum import StrEnum


class MotivoBloqueoConversacion(StrEnum):
    """Motivos sencillos y trazables para no consultar el proveedor de IA."""

    DATOS_SENSIBLES = "datos_sensibles"
    EVALUACION_NO_PERMITIDA = "evaluacion_no_permitida"
    FUERA_DE_ALCANCE = "fuera_de_alcance"


@dataclass(frozen=True)
class DecisionAlcanceConversacion:
    """Resultado de revisar una consulta antes de usar un proveedor de IA."""

    permitida: bool
    motivo: MotivoBloqueoConversacion | None = None


PALABRAS_DATOS_SENSIBLES = (
    "contraseña",
    "password",
    "cédula",
    "cedula",
    "número de documento",
    "numero de documento",
    "cuenta bancaria",
    "tarjeta de crédito",
    "tarjeta de credito",
)

EXPRESIONES_EVALUACION_NO_PERMITIDA = (
    "diagnóstico psicológico",
    "diagnostico psicologico",
    "diagnóstico profesional",
    "diagnostico profesional",
    "evalúame psicológicamente",
    "evaluame psicologicamente",
    "califica mi desempeño",
    "califique mi desempeño",
)

PALABRAS_FUERA_DE_ALCANCE = (
    "pronóstico del clima",
    "pronostico del clima",
    "resultado de fútbol",
    "resultado de futbol",
    "receta médica",
    "receta medica",
)


def evaluar_alcance_conversacion(mensaje: str) -> DecisionAlcanceConversacion:
    """Determina si una consulta puede enviarse al agente orientador.

    Las reglas son intencionalmente pequeñas, explícitas y revisables. No
    reemplazan el prompt del proveedor; impiden enviar solicitudes que el MVP
    no debe atender.
    """
    mensaje_normalizado = mensaje.lower()

    if any(palabra in mensaje_normalizado for palabra in PALABRAS_DATOS_SENSIBLES):
        return DecisionAlcanceConversacion(
            permitida=False,
            motivo=MotivoBloqueoConversacion.DATOS_SENSIBLES,
        )

    if any(
        expresion in mensaje_normalizado
        for expresion in EXPRESIONES_EVALUACION_NO_PERMITIDA
    ):
        return DecisionAlcanceConversacion(
            permitida=False,
            motivo=MotivoBloqueoConversacion.EVALUACION_NO_PERMITIDA,
        )

    if any(palabra in mensaje_normalizado for palabra in PALABRAS_FUERA_DE_ALCANCE):
        return DecisionAlcanceConversacion(
            permitida=False,
            motivo=MotivoBloqueoConversacion.FUERA_DE_ALCANCE,
        )

    return DecisionAlcanceConversacion(permitida=True)
