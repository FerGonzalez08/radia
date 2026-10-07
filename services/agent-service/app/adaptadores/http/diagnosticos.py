from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.adaptadores.http.dependencias import obtener_repositorio_diagnosticos
from app.adaptadores.http.esquemas_diagnostico import (
    DiagnosticoCreadoRespuesta,
    CompetenciaOrientativaRespuesta,
    InstrumentoActivoRespuesta,
    PreguntaInstrumentoRespuesta,
    ResultadoOrientativoRespuesta,
    SolicitudCrearDiagnostico,
)
from app.aplicacion.diagnostico.registrar_diagnostico import (
    RegistrarDiagnostico,
    RespuestaRegistroDiagnostico,
    SolicitudRegistroDiagnostico,
)
from app.aplicacion.diagnostico.consultar_resultado_orientativo import (
    ConsultarResultadoOrientativo,
    DiagnosticoNoEncontradoError,
)
from app.dominios.diagnostico.instrumento import obtener_instrumento_activo
from app.puertos.repositorio_diagnosticos import RepositorioDiagnosticos


enrutador = APIRouter(prefix="/api/v1/diagnosticos", tags=["diagnosticos"])
RepositorioDiagnosticosDependencia = Annotated[
    RepositorioDiagnosticos, Depends(obtener_repositorio_diagnosticos)
]


@enrutador.get("/instrumento-activo", response_model=InstrumentoActivoRespuesta)
def consultar_instrumento_activo() -> InstrumentoActivoRespuesta:
    """Consulta el instrumento simulado disponible para esta iteración."""
    instrumento = obtener_instrumento_activo()
    return InstrumentoActivoRespuesta(
        instrumento_id=instrumento.id,
        nombre=instrumento.nombre,
        descripcion=instrumento.descripcion,
        preguntas=[
            PreguntaInstrumentoRespuesta(
                id=pregunta.id,
                texto=pregunta.texto,
                categoria=pregunta.categoria,
            )
            for pregunta in instrumento.preguntas
        ],
    )


@enrutador.post("", response_model=DiagnosticoCreadoRespuesta, status_code=status.HTTP_201_CREATED)
def crear_diagnostico(
    solicitud_http: SolicitudCrearDiagnostico,
    repositorio: RepositorioDiagnosticosDependencia,
) -> DiagnosticoCreadoRespuesta:
    """Registra respuestas válidas sin calcular perfiles ni recomendaciones."""
    solicitud = SolicitudRegistroDiagnostico(
        instrumento_id=solicitud_http.instrumento_id,
        respuestas=tuple(
            RespuestaRegistroDiagnostico(
                pregunta_id=respuesta.pregunta_id,
                valor=respuesta.valor,
            )
            for respuesta in solicitud_http.respuestas
        ),
    )
    resultado = RegistrarDiagnostico(repositorio).ejecutar(solicitud)
    return DiagnosticoCreadoRespuesta(
        diagnostico_id=resultado.id,
        instrumento_id=resultado.instrumento_id,
        estado=resultado.estado,
        fecha_creacion=resultado.fecha_creacion,
    )


@enrutador.get(
    "/{diagnostico_id}/resultado-orientativo",
    response_model=ResultadoOrientativoRespuesta,
)
def consultar_resultado_orientativo(
    diagnostico_id: UUID,
    repositorio: RepositorioDiagnosticosDependencia,
) -> ResultadoOrientativoRespuesta:
    """Consulta una devolución calculada sin IA generativa ni datos reales."""
    try:
        resultado = ConsultarResultadoOrientativo(repositorio).ejecutar(diagnostico_id)
    except DiagnosticoNoEncontradoError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un diagnóstico con el identificador indicado.",
        ) from error

    def convertir_competencia(competencia: object) -> CompetenciaOrientativaRespuesta:
        return CompetenciaOrientativaRespuesta.model_validate(competencia, from_attributes=True)

    return ResultadoOrientativoRespuesta(
        diagnostico_id=resultado.diagnostico_id,
        instrumento_id=resultado.instrumento_id,
        fortalezas=[convertir_competencia(item) for item in resultado.fortalezas],
        oportunidades=[convertir_competencia(item) for item in resultado.oportunidades],
        aviso=(
            "Resultado orientativo generado con reglas simuladas del MVP. "
            "No corresponde a una evaluación académica, psicológica ni a una "
            "recomendación generada por inteligencia artificial."
        ),
    )
