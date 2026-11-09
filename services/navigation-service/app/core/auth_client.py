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

async def get_user(user_id: str) -> dict | None:
    users = await list_users_internal()
    return next((u for u in users if u["id"] == user_id), None)
