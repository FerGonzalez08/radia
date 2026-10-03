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


async def has_active_mentorship(user_a: str, user_b: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.NAVIGATION_SERVICE_URL}/internal/mentorships/active",
            params={"user_a": user_a, "user_b": user_b},
            headers={"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY},
        )
    if response.status_code != 200:
        return False
    return response.json().get("active", False)
