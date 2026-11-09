from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.request_id import RequestIdMiddleware
from app.core.database import Base, engine
from app.models import conversation, message, last_seen  # noqa: F401
from app.routers import chat, ws

# Las tablas se gestionan con Alembic (alembic upgrade head), no con create_all.

app = FastAPI(title="RADIA Chat Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)  # el último que se agrega es el más externo: envuelve también las respuestas de error
app.include_router(chat.router)
app.include_router(ws.router)


@app.get("/health")
def health():
    """Acceso: público (no requiere sesión)."""
    return {"status": "ok"}
