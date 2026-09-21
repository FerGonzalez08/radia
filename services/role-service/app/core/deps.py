from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth_client import validate_session
from app.core.config import ADMIN_ROLE_ID

bearer_scheme = HTTPBearer(auto_error=False)


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    session = await validate_session(credentials.credentials)

    if session.get("role_id") != str(ADMIN_ROLE_ID):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol de administrador")

    return session
