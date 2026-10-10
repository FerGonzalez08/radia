"""Caso de uso que coordina el puerto del agente conversacional."""

import logging
from dataclasses import replace

from app.dominios.conocimiento.documentos import ConsultaDocumental, FragmentoDocumental
from app.dominios.conversacion.mensajes import (
    FuenteDocumentalConsultada,
    RespuestaConversacion,
    SolicitudConversacion,
    TipoRespuestaConversacional,
)
from app.dominios.conversacion.reglas_alcance import (
    MotivoBloqueoConversacion,
    evaluar_alcance_conversacion,
)
from app.puertos.agente_conversacional import AgenteConversacional
from app.puertos.consultor_documental import ConsultorDocumental


registro = logging.getLogger(__name__)


class ConversarConAgente:
    """Solicita orientación al agente sin acoplarse al proveedor concreto."""

    def __init__(
        self,
        agente: AgenteConversacional,
        consultor_documental: ConsultorDocumental | None = None,
    ) -> None:
        self._agente = agente
        self._consultor_documental = consultor_documental

    def ejecutar(self, solicitud: SolicitudConversacion) -> RespuestaConversacion:
        """Evalúa el alcance y delega solo las consultas permitidas al puerto."""
        decision = evaluar_alcance_conversacion(solicitud.mensaje)
        if not decision.permitida:
            assert decision.motivo is not None
            return RespuestaConversacion(
                respuesta=_obtener_respuesta_segura(decision.motivo),
                recursos=(),
                tipo_respuesta=TipoRespuestaConversacional.FUERA_DE_ALCANCE,
            )
        if self._consultor_documental is None:
            return self._agente.responder(solicitud)

        try:
            resultado_documental = self._consultor_documental.consultar(
                ConsultaDocumental(pregunta=solicitud.mensaje)
            )
        except Exception:
            registro.warning("No fue posible recuperar evidencia documental para la consulta.")
            return _respuesta_sin_contexto_documental()

        if not resultado_documental.fragmentos:
            return _respuesta_sin_contexto_documental()

        if (
            resultado_documental.respuesta_orientativa
            and resultado_documental.tipo_respuesta
        ):
            return RespuestaConversacion(
                respuesta=resultado_documental.respuesta_orientativa,
                recursos=(),
                tipo_respuesta=TipoRespuestaConversacional(
                    resultado_documental.tipo_respuesta
                ),
                fuentes_documentales=_crear_fuentes_consultadas(
                    resultado_documental.fragmentos
                ),
            )

        solicitud_con_contexto = replace(
            solicitud,
            contexto_documental=_construir_contexto_documental(resultado_documental.fragmentos),
        )
        respuesta = self._agente.responder(solicitud_con_contexto)
        return replace(
            respuesta,
            fuentes_documentales=_crear_fuentes_consultadas(resultado_documental.fragmentos),
        )


def _obtener_respuesta_segura(motivo: MotivoBloqueoConversacion) -> str:
    """Devuelve un mensaje fijo sin consultar al proveedor externo."""
    respuestas = {
        MotivoBloqueoConversacion.DATOS_SENSIBLES: (
            "Por seguridad, no compartas contraseñas, documentos ni datos financieros. "
            "Puedo orientarte sobre aprendizaje y competencias sin esa información."
        ),
        MotivoBloqueoConversacion.EVALUACION_NO_PERMITIDA: (
            "No realizo evaluaciones psicológicas, profesionales ni calificaciones "
            "académicas. Puedo ofrecer orientación general sobre hábitos y competencias "
            "de aprendizaje."
        ),
        MotivoBloqueoConversacion.FUERA_DE_ALCANCE: (
            "Esta consulta está fuera del alcance del agente. Puedo apoyarte con "
            "orientación general sobre competencias y aprendizaje en Ingeniería de Sistemas."
        ),
    }
    return respuestas[motivo]


def _respuesta_sin_contexto_documental() -> RespuestaConversacion:
    """Evita respuestas sin evidencia cuando File Search está activo."""
    return RespuestaConversacion(
        respuesta=(
            "No encontré evidencia documental aprobada y suficiente para orientar esta "
            "consulta. Puedes formularla de otra manera o revisar los recursos disponibles."
        ),
        recursos=(),
        tipo_respuesta=TipoRespuestaConversacional.SIN_CONTEXTO_SUFICIENTE,
    )


def _construir_contexto_documental(fragmentos: tuple[FragmentoDocumental, ...]) -> str:
    """Limita el contexto enviado al agente para conservar respuestas trazables."""
    lineas = []
    for fragmento in fragmentos[:3]:
        ubicacion = f", {fragmento.ubicacion}" if fragmento.ubicacion else ""
        lineas.append(f"Fuente {fragmento.fuente_id}{ubicacion}: {fragmento.contenido[:500]}")
    return "\n".join(lineas)


def _crear_fuentes_consultadas(
    fragmentos: tuple[FragmentoDocumental, ...],
) -> tuple[FuenteDocumentalConsultada, ...]:
    """Elimina citas repetidas sin exponer el contenido recuperado al frontend."""
    fuentes: list[FuenteDocumentalConsultada] = []
    claves_vistas: set[tuple[str, str, str | None]] = set()
    for fragmento in fragmentos:
        clave = (fragmento.fuente_id, fragmento.referencia, fragmento.ubicacion)
        if clave in claves_vistas:
            continue
        claves_vistas.add(clave)
        fuentes.append(
            FuenteDocumentalConsultada(
                identificador=fragmento.fuente_id,
                referencia=fragmento.referencia,
                ubicacion=fragmento.ubicacion,
            )
        )
        if len(fuentes) == 3:
            break
    return tuple(fuentes)
