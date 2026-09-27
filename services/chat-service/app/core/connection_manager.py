from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # user_id (str) -> WebSocket activo. Solo vive en memoria de este proceso.
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)

    def is_online(self, user_id: str) -> bool:
        return user_id in self.active_connections

    async def send_to(self, user_id: str, payload: dict) -> bool:
        """Devuelve True si el mensaje se entregó en vivo, False si el destinatario no está conectado."""
        websocket = self.active_connections.get(user_id)
        if websocket is None:
            return False
        await websocket.send_json(payload)
        return True


manager = ConnectionManager()
