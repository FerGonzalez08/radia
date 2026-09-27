from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models import availability_slot, category, mentor_category, mentor_settings, mentorship  # noqa: F401
from app.models.category import Category
from app.routers import availability, categories, mentorships

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RADIA Navigation Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "ok"}
