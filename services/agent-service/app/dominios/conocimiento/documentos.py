"""Objetos de valor para recuperar conocimiento documental verificable."""

from dataclasses import dataclass
from enum import StrEnum


class EstadoFuenteDocumental(StrEnum):
    """Estado de una fuente antes de que el agente pueda usarla."""

    PENDIENTE_APROBACION = "pendiente_aprobacion"
    APROBADA = "aprobada"
    RETIRADA = "retirada"


@dataclass(frozen=True)
class FuenteDocumental:
    """Metadatos mínimos de una fuente candidata para File Search."""

    identificador: str
    titulo: str
    referencia: str
    estado: EstadoFuenteDocumental
    uso_permitido: str

    @property
    def disponible_para_consulta(self) -> bool:
        """Indica si la fuente puede enviarse al proveedor documental."""

        return self.estado is EstadoFuenteDocumental.APROBADA


@dataclass(frozen=True)
class ConsultaDocumental:
    """Consulta textual y fuentes aprobadas que se pueden considerar."""

    pregunta: str
    fuentes_permitidas: tuple[str, ...] = ()


@dataclass(frozen=True)
class FragmentoDocumental:
    """Fragmento recuperado con una referencia que permite su trazabilidad."""

    contenido: str
    fuente_id: str
    referencia: str
    ubicacion: str | None = None


@dataclass(frozen=True)
class ResultadoConsultaDocumental:
    """Resultado trazable de una consulta documental controlada."""

    fragmentos: tuple[FragmentoDocumental, ...] = ()
    respuesta_orientativa: str | None = None
    tipo_respuesta: str | None = None
