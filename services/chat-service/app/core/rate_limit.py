"""Límite de mensajes por usuaria (ventana deslizante en memoria, por instancia del servicio)."""
import threading
import time
from collections import deque


class MessageRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()

    def retry_after(self, user_id: str, limit: int, window_s: float = 60.0) -> int | None:
        """Registra un mensaje. Devuelve None si cabe o los segundos de espera si excede el límite."""
        if limit <= 0:
            return None
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(user_id, deque())
            while hits and now - hits[0] >= window_s:
                hits.popleft()
            if len(hits) >= limit:
                return max(1, int(window_s - (now - hits[0])) + 1)
            hits.append(now)
            return None

    def forget(self, user_id: str) -> None:
        with self._lock:
            if not self._hits.get(user_id):
                self._hits.pop(user_id, None)


message_limiter = MessageRateLimiter()
