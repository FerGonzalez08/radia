import httpx
from fastapi import HTTPException, status

from app.core.config import settings

TIMEOUT_S = 5.0
AUTH_NO_DISPONIBLE = "El servicio de autenticación no está disponible. Intenta de nuevo en unos segundos."


async def _enviar(metodo: str, url: str, mensaje: str, **kwargs) -> httpx.Response:
    """Llama a otro servicio; si no responde (caído, sin red o sin tiempo) devuelve 503 en lugar de un 500 sin controlar."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            return await client.request(metodo, url, **kwargs)
    except httpx.RequestError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, mensaje)


async def validate_session(access_token: str) -> dict:
    response = await _enviar(
        "GET", f"{settings.AUTH_SERVICE_URL}/auth/validate-session", AUTH_NO_DISPONIBLE,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code >= 500:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, AUTH_NO_DISPONIBLE)
    if response.status_code != 200:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    return response.json()


async def list_users_internal() -> list[dict]:
    response = await _enviar(
        "GET", f"{settings.AUTH_SERVICE_URL}/internal/users", AUTH_NO_DISPONIBLE,
        headers={"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY},
    )
    if response.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Auth Service unavailable")
    return response.json()


async def update_user_role_internal(user_id: str, role_id: str) -> dict:
    response = await _enviar(
        "PATCH", f"{settings.AUTH_SERVICE_URL}/internal/users/{user_id}/role", AUTH_NO_DISPONIBLE,
        headers={"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY},
        json={"role_id": role_id},
    )
    if response.status_code == 404:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if response.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Auth Service unavailable")
    return response.json()


async def cancel_mentor_mentorships_internal(mentor_id: str) -> int:
    """Pide a Navigation Service cancelar las mentorías activas de la mentora. Devuelve cuántas canceló."""
    if not settings.NAVIGATION_SERVICE_URL:
        return 0
    response = await _enviar(
        "POST", f"{settings.NAVIGATION_SERVICE_URL}/internal/mentors/{mentor_id}/cancel-mentorships",
        "El servicio de mentorías no está disponible. Intenta de nuevo en unos segundos.",
        headers={"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY},
    )
    if response.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Navigation Service unavailable")
    return response.json().get("cancelled", 0)
