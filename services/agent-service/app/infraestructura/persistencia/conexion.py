from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def obtener_url_base_datos() -> str:
    """Obtiene la conexión configurada para PostgreSQL."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://agente:agente@base_datos:5432/agente_orientacion",
    )


motor = create_engine(obtener_url_base_datos(), pool_pre_ping=True)
FabricaSesion = sessionmaker(bind=motor, autocommit=False, autoflush=False)


def obtener_sesion() -> Generator[Session, None, None]:
    """Entrega una sesión y garantiza su cierre al terminar la solicitud."""
    sesion = FabricaSesion()
    try:
        yield sesion
    finally:
        sesion.close()
