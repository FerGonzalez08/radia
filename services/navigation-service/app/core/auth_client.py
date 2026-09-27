import httpx
from fastapi import HTTPException, status

from app.core.config import settings


async def validate_session(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.AUTH_SERVICE_URL}/auth/validate-session",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if response.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    return response.json()


async def list_users_internal() -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.AUTH_SERVICE_URL}/internal/users",
            headers={"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY},
        )
    if response.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Auth Service unavailable")
    return response.json()
