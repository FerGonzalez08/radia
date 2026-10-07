"""Puerto de salida para recuperar fragmentos de fuentes documentales."""

from typing import Protocol

from app.dominios.conocimiento.documentos import (
    ConsultaDocumental,
    ResultadoConsultaDocumental,
)


class ConsultorDocumental(Protocol):
    """Contrato intercambiable para File Search u otra búsqueda autorizada."""

    def consultar(self, consulta: ConsultaDocumental) -> ResultadoConsultaDocumental:
        """Recupera fragmentos trazables de fuentes previamente aprobadas."""
