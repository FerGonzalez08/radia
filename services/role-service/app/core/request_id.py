"""Identificador de correlación por petición (X-Request-ID) para seguir una operación entre servicios (TC-NFR-10).

Si la petición trae X-Request-ID válido se conserva; si no, se genera uno. Se devuelve en la respuesta, se escribe en el
registro de accesos y los servicios lo reenvían en las llamadas que hacen a otros servicios.
"""
import logging
import re
import time
import uuid
from contextvars import ContextVar

HEADER = "X-Request-ID"
_VALIDO = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("uvicorn.error")


class RequestIdMiddleware:
    """Middleware ASGI puro: solo actúa sobre peticiones HTTP, los WebSocket pasan sin tocarse."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        entrante = dict(scope["headers"]).get(HEADER.lower().encode(), b"").decode("latin-1")
        request_id = entrante if _VALIDO.match(entrante) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        inicio = time.perf_counter()
        estado = {"codigo": 500}

        async def send_con_id(message):
            if message["type"] == "http.response.start":
                estado["codigo"] = message["status"]
                message.setdefault("headers", []).append((HEADER.lower().encode(), request_id.encode()))
            await send(message)

        try:
            await self.app(scope, receive, send_con_id)
        finally:
            logger.info(
                "request_id=%s %s %s -> %s (%.0f ms)",
                request_id, scope["method"], scope["path"], estado["codigo"], (time.perf_counter() - inicio) * 1000,
            )
            request_id_var.reset(token)
