"""Rutas HTTP del módulo conversacional."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.adaptadores.http.esquemas_conversacion import (
    FuenteDocumentalRespuesta,
    RecursoConversacionRespuesta,
    RespuestaConversacionSalida,
    SolicitudConversacionEntrada,
)
from app.aplicacion.conversacion.conversar_con_agente import ConversarConAgente
from app.aplicacion.diagnostico.consultar_resultado_orientativo import (
    ConsultarResultadoOrientativo,
    DiagnosticoNoEncontradoError,
)
from app.adaptadores.http.dependencias import obtener_repositorio_diagnosticos
from app.dominios.conversacion.mensajes import SolicitudConversacion
from app.infraestructura.ia.fabrica_agentes import (
    crear_agente_conversacional,
    obtener_proveedor_activo,
)
from app.infraestructura.ia.errores import (
    ConfiguracionProveedorInvalidaError,
    ProveedorIAIndisponibleError,
)
from app.infraestructura.conocimiento.fabrica_consultor_documental import (
    crear_consultor_documental_opcional,
)
from app.puertos.repositorio_diagnosticos import RepositorioDiagnosticos


enrutador = APIRouter(prefix="/api/v1/conversaciones", tags=["conversaciones"])
RepositorioDiagnosticosDependencia = Annotated[
    RepositorioDiagnosticos, Depends(obtener_repositorio_diagnosticos)
]


def construir_contexto_diagnostico(
    repositorio: RepositorioDiagnosticos, diagnostico_id: UUID
) -> str:
    """Reduce el diagnóstico a información orientativa mínima para el proveedor."""
    resultado = ConsultarResultadoOrientativo(repositorio).ejecutar(diagnostico_id)
    fortalezas = ", ".join(item.nombre for item in resultado.fortalezas) or "sin fortalezas destacadas"
    oportunidades = ", ".join(item.nombre for item in resultado.oportunidades) or "sin oportunidades destacadas"
    return (
        f"Fortalezas orientativas: {fortalezas}. "
        f"Oportunidades de fortalecimiento: {oportunidades}."
    )


@enrutador.post("", response_model=RespuestaConversacionSalida, status_code=status.HTTP_200_OK)
def crear_conversacion(
    solicitud_http: SolicitudConversacionEntrada,
    repositorio: RepositorioDiagnosticosDependencia,
) -> RespuestaConversacionSalida:
    """Envía un mensaje al agente configurado sin persistir conversaciones."""
    try:
        contexto_diagnostico = None
        if solicitud_http.diagnostico_id:
            contexto_diagnostico = construir_contexto_diagnostico(
                repositorio, solicitud_http.diagnostico_id
            )
        agente = crear_agente_conversacional()
        consultor_documental = crear_consultor_documental_opcional()
        resultado = ConversarConAgente(agente, consultor_documental).ejecutar(
            SolicitudConversacion(
                sesion_id=solicitud_http.sesion_id,
                mensaje=solicitud_http.mensaje,
                diagnostico_id=solicitud_http.diagnostico_id,
                contexto_diagnostico=contexto_diagnostico,
            )
        )
    except DiagnosticoNoEncontradoError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un diagnóstico con el identificador indicado.",
        ) from error
    except ConfiguracionProveedorInvalidaError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except ProveedorIAIndisponibleError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error

    return RespuestaConversacionSalida(
        tipo_respuesta=resultado.tipo_respuesta,
        respuesta=resultado.respuesta,
        recursos=[
            RecursoConversacionRespuesta.model_validate(recurso, from_attributes=True)
            for recurso in resultado.recursos
        ],
        fuentes_documentales=[
            FuenteDocumentalRespuesta.model_validate(fuente, from_attributes=True)
            for fuente in resultado.fuentes_documentales
        ],
        aviso_alcance=resultado.aviso_alcance,
        proveedor_modelo=obtener_proveedor_activo(),
    )
