import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adaptadores.http.conversaciones import enrutador as enrutador_conversaciones
from app.adaptadores.http.diagnosticos import enrutador as enrutador_diagnosticos

aplicacion = FastAPI(
    title="API del agente de orientación",
    version="0.1.0",
    description="API base del MVP del agente conversacional del proyecto RADIA.",
)


def obtener_origenes_cors() -> list[str]:
    """Obtiene los orígenes autorizados para las interfaces del agente."""
    valor = os.getenv(
        "ORIGENES_CORS",
        "http://localhost:3000,http://localhost:5173",
    )
    return [origen.strip() for origen in valor.split(",") if origen.strip()]

aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=obtener_origenes_cors(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

aplicacion.include_router(enrutador_diagnosticos)
aplicacion.include_router(enrutador_conversaciones)


@aplicacion.get("/api/v1/salud", tags=["salud"])
def consultar_salud() -> dict[str, str]:
    """Confirma que la API está disponible para recibir solicitudes."""
    return {"estado": "disponible"}
