"""Puerto de salida para obtener orientación conversacional."""

from typing import Protocol

from app.dominios.conversacion.mensajes import RespuestaConversacion, SolicitudConversacion


class AgenteConversacional(Protocol):
    """Contrato que permite intercambiar el proveedor del agente."""

    def responder(self, solicitud: SolicitudConversacion) -> RespuestaConversacion:
        """Genera una respuesta orientativa para el mensaje recibido."""
