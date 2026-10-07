from typing import TYPE_CHECKING, Protocol
from uuid import UUID

if TYPE_CHECKING:
    from app.aplicacion.diagnostico.registrar_diagnostico import (
        DiagnosticoRegistrado,
        SolicitudRegistroDiagnostico,
    )
    from app.aplicacion.diagnostico.consultar_resultado_orientativo import (
        DiagnosticoConRespuestas,
    )


class RepositorioDiagnosticos(Protocol):
    """Contrato de persistencia requerido por el caso de uso de diagnóstico."""

    def guardar(
        self, solicitud: "SolicitudRegistroDiagnostico"
    ) -> "DiagnosticoRegistrado":
        """Persiste un diagnóstico validado y devuelve su registro mínimo."""

    def obtener_por_id(self, diagnostico_id: UUID) -> "DiagnosticoConRespuestas | None":
        """Obtiene un diagnóstico y sus respuestas para una consulta posterior."""
