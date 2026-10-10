from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infraestructura.persistencia.conexion import obtener_sesion
from app.infraestructura.persistencia.repositorio_diagnosticos import (
    RepositorioDiagnosticosSqlAlchemy,
)
from app.puertos.repositorio_diagnosticos import RepositorioDiagnosticos


SesionBaseDatos = Annotated[Session, Depends(obtener_sesion)]


def obtener_repositorio_diagnosticos(
    sesion: SesionBaseDatos,
) -> RepositorioDiagnosticos:
    """Construye el adaptador de persistencia para una solicitud HTTP."""
    return RepositorioDiagnosticosSqlAlchemy(sesion)
