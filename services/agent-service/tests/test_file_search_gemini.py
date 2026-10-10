"""Pruebas del adaptador de Gemini File Search sin llamadas externas."""

from dataclasses import dataclass
from pathlib import Path

from app.dominios.conocimiento.documentos import ConsultaDocumental
from app.infraestructura.conocimiento.administrar_file_search import (
    cargar_archivo,
    crear_almacen,
)
from app.infraestructura.conocimiento.gemini_file_search import ConsultorDocumentalGemini


@dataclass
class CitaFalsa:
    type: str
    file_name: str
    source: str
    document_uri: str | None = None
    page_number: int | None = None


@dataclass
class BloqueFalso:
    type: str
    text: str
    annotations: list[CitaFalsa]


@dataclass
class PasoFalso:
    type: str
    content: list[BloqueFalso]


@dataclass
class InteraccionFalsa:
    steps: list[PasoFalso]
    output_text: str = "Orientación basada en la fuente."


class InteraccionesFalsas:
    """Registra los parámetros recibidos sin comunicarse con Gemini."""

    def __init__(self) -> None:
        self.parametros: dict[str, object] | None = None

    def create(self, **parametros: object) -> InteraccionFalsa:
        self.parametros = parametros
        return InteraccionFalsa(
            steps=[
                PasoFalso(
                    type="model_output",
                    content=[
                        BloqueFalso(
                            type="text",
                            text="La fuente describe brechas educativas de género.",
                            annotations=[
                                CitaFalsa(
                                    type="file_citation",
                                    file_name="FCD-001.pdf",
                                    source="Contenido recuperado que no debe exponerse como referencia.",
                                    document_uri="fileSearchStores/agente-radia/documents/fcd-001",
                                    page_number=1,
                                )
                            ],
                        )
                    ],
                )
            ]
        )


class ClienteConsultaFalso:
    def __init__(self) -> None:
        self.interactions = InteraccionesFalsas()


class OperacionFalsa:
    done = True
    name = "operations/carga-fcd-001"


class AlmacenesFalsos:
    def __init__(self) -> None:
        self.parametros_carga: dict[str, object] | None = None

    def create(self, **parametros: object) -> object:
        return type("Almacen", (), {"name": "fileSearchStores/agente-radia"})()

    def upload_to_file_search_store(self, **parametros: object) -> OperacionFalsa:
        self.parametros_carga = parametros
        return OperacionFalsa()


class ClienteAdministradorFalso:
    def __init__(self) -> None:
        self.file_search_stores = AlmacenesFalsos()
        self.operations = object()


def test_consultor_recupera_fragmento_con_cita() -> None:
    """La búsqueda conserva referencia y página para explicar la respuesta."""
    cliente = ClienteConsultaFalso()
    consultor = ConsultorDocumentalGemini(
        cliente=cliente,
        almacen="fileSearchStores/agente-radia",
        modelo="gemini-prueba",
    )

    resultado = consultor.consultar(ConsultaDocumental(pregunta="¿Qué plantea la fuente?"))

    assert len(resultado.fragmentos) == 1
    assert resultado.respuesta_orientativa == "Orientación basada en la fuente."
    assert resultado.tipo_respuesta == "orientacion"
    assert resultado.fragmentos[0].fuente_id == "FCD-001.pdf"
    assert resultado.fragmentos[0].referencia == (
        "fileSearchStores/agente-radia/documents/fcd-001"
    )
    assert resultado.fragmentos[0].ubicacion == "página 1"
    assert cliente.interactions.parametros is not None
    assert cliente.interactions.parametros["model"] == "gemini-prueba"
    assert "¿Qué plantea la fuente?" in str(cliente.interactions.parametros["input"])
    assert cliente.interactions.parametros["tools"] == [
        {
            "type": "file_search",
            "file_search_store_names": ["fileSearchStores/agente-radia"],
        }
    ]


def test_administrador_prepara_carga_explicita_de_un_archivo(tmp_path: Path) -> None:
    """La carga solo ocurre al ejecutar el comando y recibir una ruta válida."""
    archivo = tmp_path / "FCD-001.pdf"
    archivo.write_text("Documento de prueba", encoding="utf-8")
    cliente = ClienteAdministradorFalso()

    almacen = crear_almacen(cliente, "agente-radia")
    operacion = cargar_archivo(cliente, almacen, archivo)

    assert almacen == "fileSearchStores/agente-radia"
    assert operacion == "operations/carga-fcd-001"
    assert cliente.file_search_stores.parametros_carga == {
        "file": str(archivo),
        "file_search_store_name": "fileSearchStores/agente-radia",
        "config": {"display_name": "FCD-001.pdf"},
    }
