import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    """Hora actual en UTC, calculada por la aplicación al insertar.

    Las columnas created_at de login_attempts, refresh_tokens y verification_tokens se crearon en la migración inicial con
    server_default='now()' como TEXTO, y PostgreSQL lo evaluó una sola vez al crear la tabla: sin un valor explícito, todas
    las filas quedan con la fecha de creación de la tabla y fallan el bloqueo por intentos y los límites por hora.
    """
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def uuid_pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
