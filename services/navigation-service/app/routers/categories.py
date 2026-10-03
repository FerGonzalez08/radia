import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_client import list_users_internal
from app.core.config import MENTOR_ROLE_ID
from app.core.database import get_db
from app.core.deps import get_current_session, require_admin, require_mentor
from app.models.category import Category
from app.models.mentor_category import MentorCategory
from app.schemas.category import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    MentorCategoriesUpdate,
    MentorSearchResult,
)

router = APIRouter(tags=["categories"])


# --- Catálogo (RQF-024, solo administrador) ---

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), _session: dict = Depends(get_current_session)):
    return db.query(Category).order_by(Category.name).all()


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    existing = db.query(Category).filter(Category.name == payload.name).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una categoría con ese nombre")

    category = Category(name=payload.name, description=payload.description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")

    if payload.name is not None:
        category.name = payload.name
    if payload.description is not None:
        category.description = payload.description

    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")

    in_use = db.query(MentorCategory).filter(MentorCategory.category_id == category_id).first()
    if in_use is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede eliminar una categoría en uso")

    db.delete(category)
    db.commit()
    return None


# --- Selección de categorías por la mentora (RQF-031) ---

@router.get("/mentors/me/categories", response_model=list[CategoryOut])
def get_my_categories(
    db: Session = Depends(get_db),
    session: dict = Depends(require_mentor),
):
    mentor_id = uuid.UUID(session["user_id"])
    return (
        db.query(Category)
        .join(MentorCategory, MentorCategory.category_id == Category.id)
        .filter(MentorCategory.mentor_user_id == mentor_id)
        .all()
    )


@router.put("/mentors/me/categories", response_model=list[CategoryOut])
def set_my_categories(
    payload: MentorCategoriesUpdate,
    db: Session = Depends(get_db),
    session: dict = Depends(require_mentor),
):
    mentor_id = uuid.UUID(session["user_id"])

    valid_ids = {c.id for c in db.query(Category.id).filter(Category.id.in_(payload.category_ids)).all()}
    invalid = set(payload.category_ids) - valid_ids
    if invalid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Categorías inválidas: {invalid}")

    # Reemplaza el set completo — más simple que hacer add/remove incremental.
    db.query(MentorCategory).filter(MentorCategory.mentor_user_id == mentor_id).delete()
    for category_id in payload.category_ids:
        db.add(MentorCategory(mentor_user_id=mentor_id, category_id=category_id))
    db.commit()

    return db.query(Category).filter(Category.id.in_(payload.category_ids)).all()


# --- Búsqueda de mentoras por categoría (RQF-027) ---

@router.get("/search/mentors", response_model=list[MentorSearchResult])
async def search_mentors(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    _session: dict = Depends(get_current_session),
):
    mentor_links = db.query(MentorCategory).filter(MentorCategory.category_id == category_id).all()
    matching_mentor_ids = {str(link.mentor_user_id) for link in mentor_links}

    if not matching_mentor_ids:
        return []

    all_users = await list_users_internal()
    results = []
    for user in all_users:
        if user["id"] not in matching_mentor_ids or user["role_id"] != str(MENTOR_ROLE_ID):
            continue
        mentor_categories = (
            db.query(Category.name)
            .join(MentorCategory, MentorCategory.category_id == Category.id)
            .filter(MentorCategory.mentor_user_id == uuid.UUID(user["id"]))
            .all()
        )
        results.append(MentorSearchResult(
            mentor_user_id=user["id"],
            nombre=user["nombre"],
            email=user["email"],
            categories=[c[0] for c in mentor_categories],
        ))
    return results
