import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.internal_auth import verify_internal_key
from app.models.user import User
from app.schemas.user import RoleUpdateRequest, UserOut

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/users", response_model=list[UserOut])
def list_users_internal(
    db: Session = Depends(get_db),
    _key: None = Depends(verify_internal_key),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role_internal(
    user_id: uuid.UUID,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    _key: None = Depends(verify_internal_key),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    user.role_id = payload.role_id
    db.commit()
    db.refresh(user)
    return user
