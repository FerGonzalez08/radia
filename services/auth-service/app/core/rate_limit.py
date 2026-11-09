"""Límite de frecuencia por IP (ventana deslizante en memoria) para los endpoints públicos de auth-service.

Cada instancia del servicio lleva su propio contador. Con una sola instancia (despliegue del MVP) el límite es exacto;
con varias, el límite efectivo es por instancia. Los umbrales se configuran por variable de entorno (config.py).
"""
import threading
import time
from collections import deque

from fastapi import HTTPException, Request, status

from app.core.config import settings


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()

    def retry_after(self, key: str, limit: int, window_s: float) -> int | None:
        """Registra una petición. Devuelve None si cabe en el límite o los segundos de espera si lo excede."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] >= window_s:
                hits.popleft()
            if len(hits) >= limit:
                return max(1, int(window_s - (now - hits[0])) + 1)
            hits.append(now)
            if len(self._hits) > 10_000:  # evita crecimiento sin límite: descarta claves vacías
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]
            return None


limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    """IP del cliente. Detrás de Azure App Service el último valor de X-Forwarded-For lo agrega el balanceador de Azure
    (los anteriores pueden venir falsificados por el cliente), y puede traer el puerto («ip:puerto»)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        last = forwarded.split(",")[-1].strip()
        return last.rsplit(":", 1)[0] if last.count(":") == 1 else last
    return request.client.host if request.client else "unknown"


def rate_limit(scope: str, limit_setting: str):
    """Dependencia de FastAPI: responde 429 con Retry-After si la IP excede el umbral del ámbito."""

    def dependency(request: Request) -> None:
        limit = getattr(settings, limit_setting)
        if limit <= 0:  # 0 desactiva el límite
            return
        wait = limiter.retry_after(f"{scope}:{client_ip(request)}", limit, 60)
        if wait is not None:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Demasiadas solicitudes. Intenta de nuevo en {wait} segundo(s).",
                headers={"Retry-After": str(wait)},
            )

    return dependency
