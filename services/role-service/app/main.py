from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID, settings
from app.core.database import Base, SessionLocal, engine
from app.models.role import Role
from app.routers import roles

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RADIA Role Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(roles.router)


@app.on_event("startup")
def seed_roles():
    db: Session = SessionLocal()
    try:
        seed_data = [
            (MENTEE_ROLE_ID, "estudiante", "Rol inicial asignado automáticamente al registrarse"),
            (MENTOR_ROLE_ID, "mentora", "Asignado manualmente por un administrador"),
            (ADMIN_ROLE_ID, "administrador", "Gestiona el catálogo de roles y usuarios"),
        ]
        for role_id, name, description in seed_data:
            if db.query(Role).filter(Role.id == role_id).first() is None:
                db.add(Role(id=role_id, name=name, description=description))
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
