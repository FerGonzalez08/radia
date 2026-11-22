import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.internal_auth import verify_internal_key
from app.models.user import User
from app.schemas.user import RoleUpdateRequest, UserOut

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/users", response_model=list[UserOut])
def list_users_internal(
    q: str | None = Query(default=None, max_length=100, description="Texto a buscar en nombre o correo"),
    role_id: uuid.UUID | None = Query(default=None, description="Filtra por rol"),
    limit: int | None = Query(default=None, ge=1, le=500, description="Máximo de filas; sin valor devuelve todas"),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _key: None = Depends(verify_internal_key),
):
    """Lista usuarias, de la más reciente a la más antigua. Sin parámetros devuelve todas (comportamiento previo); con
    q, role_id, limit y offset filtra y pagina en la base de datos (TC-NFR-09).

    Acceso: interno entre servicios (cabecera X-Internal-Service-Key); no es para usuarias finales.
    """
    query = db.query(User)
    if q:
        patron = f"%{q.strip()}%"
        query = query.filter(User.nombre.ilike(patron) | User.email.ilike(patron))
    if role_id is not None:
        query = query.filter(User.role_id == role_id)
    query = query.order_by(User.created_at.desc(), User.id)
    if limit is not None:
        query = query.offset(offset).limit(limit)
    return query.all()


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role_internal(
    user_id: uuid.UUID,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    _key: None = Depends(verify_internal_key),
):
    """Acceso: interno entre servicios (cabecera X-Internal-Service-Key); no es para usuarias finales."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    user.role_id = payload.role_id
    db.commit()
    db.refresh(user)
    return user
