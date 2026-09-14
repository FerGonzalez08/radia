import uuid
from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, uuid_pk


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Datos personales requeridos por RQF-001/RQF-023.
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    sexo: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)

    # Referencia lógica al Role Management Service — sin FK física,
    # sin enum: ese catálogo no vive en esta base de datos.
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
