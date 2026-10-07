from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infraestructura.persistencia.base import Base


class Diagnostico(Base):
    """Registro técnico de un diagnóstico inicial sin datos personales."""

    __tablename__ = "diagnosticos"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    instrumento_id: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="registrado")
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    respuestas: Mapped[list[RespuestaDiagnostico]] = relationship(
        back_populates="diagnostico", cascade="all, delete-orphan"
    )


class RespuestaDiagnostico(Base):
    """Respuesta asociada a una pregunta del instrumento simulado."""

    __tablename__ = "respuestas_diagnostico"
    __table_args__ = (
        UniqueConstraint(
            "diagnostico_id", "pregunta_id", name="uq_respuesta_diagnostico_pregunta"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    diagnostico_id: Mapped[UUID] = mapped_column(
        ForeignKey("diagnosticos.id", ondelete="CASCADE"), nullable=False
    )
    pregunta_id: Mapped[str] = mapped_column(String(30), nullable=False)
    valor: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    diagnostico: Mapped[Diagnostico] = relationship(back_populates="respuestas")
