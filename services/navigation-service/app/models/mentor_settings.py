import uuid

from sqlalchemy import Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MentorSettings(Base):
    __tablename__ = "mentor_settings"

    # PK es el propio user_id de la mentora — una fila por mentora, sin id separado.
    mentor_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    auto_accept: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weekly_limit: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
