"""Pruebas de las reglas básicas para usar fuentes documentales."""

from app.dominios.conocimiento.documentos import (
    EstadoFuenteDocumental,
    FuenteDocumental,
)


def crear_fuente(estado: EstadoFuenteDocumental) -> FuenteDocumental:
    """Construye una fuente mínima para validar sus estados."""

    return FuenteDocumental(
        identificador="FCD-001",
        titulo="Fuente de prueba",
        referencia="https://ejemplo.edu.co/fuente",
        estado=estado,
        uso_permitido="Prueba técnica.",
    )


def test_fuente_aprobada_puede_consultarse() -> None:
    """Solo una fuente aprobada llega al adaptador documental."""

    assert crear_fuente(EstadoFuenteDocumental.APROBADA).disponible_para_consulta


def test_fuente_pendiente_o_retirada_no_puede_consultarse() -> None:
    """Las fuentes no aprobadas se excluyen antes de llamar al proveedor."""

    assert not crear_fuente(EstadoFuenteDocumental.PENDIENTE_APROBACION).disponible_para_consulta
    assert not crear_fuente(EstadoFuenteDocumental.RETIRADA).disponible_para_consulta
