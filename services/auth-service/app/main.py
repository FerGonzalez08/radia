from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth

# Crea las tablas si no existen. Válido para desarrollo local;
# en producción esto se reemplaza por migraciones de Alembic.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RADIA Auth Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
