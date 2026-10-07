from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.aplicacion.diagnostico.consultar_resultado_orientativo import (
    DiagnosticoConRespuestas,
    RespuestaDiagnosticoRegistrada,
)
from app.aplicacion.diagnostico.registrar_diagnostico import (
    DiagnosticoRegistrado,
    SolicitudRegistroDiagnostico,
)
from app.infraestructura.persistencia.modelos import Diagnostico, RespuestaDiagnostico


class RepositorioDiagnosticosSqlAlchemy:
    """Adaptador de salida para persistir diagnósticos con SQLAlchemy."""

    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def guardar(self, solicitud: SolicitudRegistroDiagnostico) -> DiagnosticoRegistrado:
        """Guarda un diagnóstico y sus respuestas en una única transacción."""
        diagnostico = Diagnostico(
            instrumento_id=solicitud.instrumento_id,
            estado="registrado",
            respuestas=[
                RespuestaDiagnostico(
                    pregunta_id=respuesta.pregunta_id,
                    valor=respuesta.valor,
                )
                for respuesta in solicitud.respuestas
            ],
        )
        self._sesion.add(diagnostico)
        self._sesion.commit()
        self._sesion.refresh(diagnostico)

        return DiagnosticoRegistrado(
            id=diagnostico.id,
            instrumento_id=diagnostico.instrumento_id,
            estado=diagnostico.estado,
            fecha_creacion=diagnostico.fecha_creacion,
        )

    def obtener_por_id(self, diagnostico_id: UUID) -> DiagnosticoConRespuestas | None:
        """Recupera un diagnóstico con sus respuestas sin exponer entidades ORM."""
        consulta = (
            select(Diagnostico)
            .options(selectinload(Diagnostico.respuestas))
            .where(Diagnostico.id == diagnostico_id)
        )
        diagnostico = self._sesion.scalar(consulta)
        if diagnostico is None:
            return None

        return DiagnosticoConRespuestas(
            id=diagnostico.id,
            instrumento_id=diagnostico.instrumento_id,
            estado=diagnostico.estado,
            respuestas=tuple(
                RespuestaDiagnosticoRegistrada(
                    pregunta_id=respuesta.pregunta_id,
                    valor=respuesta.valor,
                )
                for respuesta in diagnostico.respuestas
            ),
        )
