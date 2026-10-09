from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.dominios.diagnostico.instrumento import INSTRUMENTO_ACTIVO, ids_preguntas_activas


class RespuestaDiagnosticoEntrada(BaseModel):
    """Contrato JSON de una respuesta del diagnóstico inicial."""

    pregunta_id: str = Field(min_length=1, max_length=30)
    valor: int = Field(ge=1, le=5)


class SolicitudCrearDiagnostico(BaseModel):
    """Contrato JSON para registrar todas las respuestas del instrumento activo."""

    instrumento_id: str = Field(min_length=1, max_length=100)
    respuestas: list[RespuestaDiagnosticoEntrada] = Field(min_length=1)

    @field_validator("instrumento_id")
    @classmethod
    def validar_instrumento_activo(cls, instrumento_id: str) -> str:
        """Rechaza instrumentos distintos al publicado por el MVP."""
        if instrumento_id != INSTRUMENTO_ACTIVO.id:
            raise ValueError("El instrumento debe corresponder al instrumento activo.")
        return instrumento_id

    @model_validator(mode="after")
    def validar_respuestas_completas(self) -> "SolicitudCrearDiagnostico":
        """Exige una respuesta única para cada pregunta activa."""
        identificadores = [respuesta.pregunta_id for respuesta in self.respuestas]
        if len(identificadores) != len(set(identificadores)):
            raise ValueError("No se permiten preguntas repetidas.")

        identificadores_esperados = ids_preguntas_activas()
        identificadores_recibidos = set(identificadores)
        if identificadores_recibidos != identificadores_esperados:
            faltantes = sorted(identificadores_esperados - identificadores_recibidos)
            desconocidos = sorted(identificadores_recibidos - identificadores_esperados)
            detalle = []
            if faltantes:
                detalle.append(f"Faltan preguntas: {', '.join(faltantes)}.")
            if desconocidos:
                detalle.append(f"Preguntas no permitidas: {', '.join(desconocidos)}.")
            raise ValueError(" ".join(detalle))
        return self


class PreguntaInstrumentoRespuesta(BaseModel):
    """Representación pública de una pregunta del instrumento simulado."""

    id: str
    texto: str
    categoria: str
    escala_minima: int = 1
    escala_maxima: int = 5


class InstrumentoActivoRespuesta(BaseModel):
    """Contrato de salida del instrumento publicado por el MVP."""

    instrumento_id: str
    nombre: str
    descripcion: str
    preguntas: list[PreguntaInstrumentoRespuesta]


class DiagnosticoCreadoRespuesta(BaseModel):
    """Respuesta mínima emitida al registrar un diagnóstico."""

    diagnostico_id: UUID
    instrumento_id: str
    estado: str
    fecha_creacion: datetime


class CompetenciaOrientativaRespuesta(BaseModel):
    """Competencia presentada en la devolución orientativa simulada."""

    pregunta_id: str
    nombre: str
    categoria: str
    puntaje: int = Field(ge=1, le=5)
    clasificacion: str
    recurso_simulado: str


class ResultadoOrientativoRespuesta(BaseModel):
    """Contrato de salida para una devolución sin IA generativa."""

    diagnostico_id: UUID
    instrumento_id: str
    fortalezas: list[CompetenciaOrientativaRespuesta]
    oportunidades: list[CompetenciaOrientativaRespuesta]
    aviso: str
