import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.request_id import RequestIdMiddleware
from app.core.database import Base, engine
from app.core.retention import purge_loop
from app.routers import auth, internal



# Crea las tablas si no existen. Válido para desarrollo local;
# en producción esto se reemplaza por migraciones de Alembic.
# Las tablas ahora se gestionan con Alembic (alembic upgrade head), no con
# create_all — ver alembic/versions. Se deja este comentario para que quede
# explícito que el cambio fue intencional.

@asynccontextmanager
async def lifespan(_: FastAPI):
    tarea = asyncio.create_task(purge_loop())  # TC-SEG-17: depuración periódica de datos de seguridad vencidos
    yield
    tarea.cancel()


app = FastAPI(title="RADIA Auth Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)  # el último que se agrega es el más externo: envuelve también las respuestas de error

app.include_router(auth.router)
app.include_router(internal.router)


@app.get("/health")
def health():
    """Acceso: público (no requiere sesión)."""
    return {"status": "ok"}
