"""Crear tablas iniciales de diagnóstico.

Revision ID: 20260918_01
Revises:
Create Date: 2026-09-18 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260918_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea tablas para diagnósticos y respuestas sin datos personales."""
    op.create_table(
        "diagnosticos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("instrumento_id", sa.String(length=100), nullable=False),
        sa.Column("estado", sa.String(length=30), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "respuestas_diagnostico",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("diagnostico_id", sa.Uuid(), nullable=False),
        sa.Column("pregunta_id", sa.String(length=30), nullable=False),
        sa.Column("valor", sa.Integer(), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["diagnostico_id"], ["diagnosticos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("diagnostico_id", "pregunta_id", name="uq_respuesta_diagnostico_pregunta"),
    )


def downgrade() -> None:
    """Elimina las tablas de diagnóstico de la versión inicial."""
    op.drop_table("respuestas_diagnostico")
    op.drop_table("diagnosticos")
