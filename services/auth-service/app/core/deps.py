import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import ADMIN_ROLE_ID, KNOWN_ROLE_IDS
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.refresh_token import RefreshToken
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
SIN_ROL_MENSAJE = "Tu cuenta aún no tiene un rol asignado. Contacta a una administradora."


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user_id = uuid.UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()

    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    # TC-AUT-17: si el token trae la sesión (sid), esa sesión debe seguir abierta (no cerrada ni revocada).
    sid = payload.get("sid")
    if sid is not None:
        try:
            family_id = uuid.UUID(sid)
        except ValueError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
        abierta = db.query(RefreshToken.id).filter(
            RefreshToken.family_id == family_id,
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        ).first()
        if abierta is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session closed")

    # TC-AUT-23: una cuenta sin rol válido asignado queda bloqueada hasta que una administradora le asigne uno.
    if user.role_id not in KNOWN_ROLE_IDS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, SIN_ROL_MENSAJE)

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role_id != ADMIN_ROLE_ID:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol de administrador")
    return current_user