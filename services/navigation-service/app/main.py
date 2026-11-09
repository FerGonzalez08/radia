from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.request_id import RequestIdMiddleware
from app.core.database import Base, SessionLocal, engine
from app.models import availability_slot, category, mentor_category, mentor_settings, mentorship  # noqa: F401
from app.models.category import Category
from app.routers import availability, categories, mentorships

# Las tablas se gestionan con Alembic (alembic upgrade head), no con create_all.

app = FastAPI(title="RADIA Navigation Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)  # el último que se agrega es el más externo: envuelve también las respuestas de error

app.include_router(categories.router)
app.include_router(availability.router)
app.include_router(mentorships.router)

@app.on_event("startup")
def seed_categories():
    db: Session = SessionLocal()
    try:
        defaults = ["Python", "JavaScript", "React", "Java", "Bases de datos", "Diseño UX/UI"]
        for name in defaults:
            if db.query(Category).filter(Category.name == name).first() is None:
                db.add(Category(name=name))
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    """Acceso: público (no requiere sesión)."""
    return {"status": "ok"}
