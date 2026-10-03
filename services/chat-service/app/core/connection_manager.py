from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # user_id (str) -> lista de WebSockets activos (una persona puede tener
        # varias pestañas/dispositivos conectados a la vez).
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> bool:
        """Devuelve True si esa desconexión dejó al usuario sin ninguna sesión activa."""
        connections = self.active_connections.get(user_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self.active_connections.pop(user_id, None)
            return True
        return False

    def is_online(self, user_id: str) -> bool:
        return bool(self.active_connections.get(user_id))

    async def send_to(self, user_id: str, payload: dict) -> bool:
        """Devuelve True si se entregó a al menos una sesión activa del destinatario."""
        connections = self.active_connections.get(user_id, [])
        if not connections:
            return False

        delivered = False
        for websocket in list(connections):
            try:
                await websocket.send_json(payload)
                delivered = True
            except Exception:
                # Una conexión rota no debe tumbar el envío a las demás sesiones del usuario.
                connections.remove(websocket)
        return delivered


manager = ConnectionManager()
