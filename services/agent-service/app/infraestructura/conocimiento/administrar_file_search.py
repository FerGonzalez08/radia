"""Comando explícito para administrar un almacén Gemini File Search."""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Protocol


class AlmacenesFileSearch(Protocol):
    """Operaciones necesarias para crear, cargar y listar documentos."""

    def create(self, **parametros: object) -> object:
        """Crea un almacén documental."""

    def upload_to_file_search_store(self, **parametros: object) -> object:
        """Carga un archivo a un almacén existente."""

    def documents(self) -> object:
        """Expone documentos gestionados por el almacén."""


class ClienteAdministradorFileSearch(Protocol):
    """Cliente mínimo para administrar File Search sin acoplar el SDK en pruebas."""

    file_search_stores: AlmacenesFileSearch
    operations: object


def crear_almacen(cliente: ClienteAdministradorFileSearch, nombre: str) -> str:
    """Crea un almacén con embeddings de texto y devuelve su identificador."""
    almacen = cliente.file_search_stores.create(
        config={
            "display_name": nombre,
            "embedding_model": "models/gemini-embedding-2",
        }
    )
    return str(getattr(almacen, "name"))


def cargar_archivo(
    cliente: ClienteAdministradorFileSearch,
    almacen: str,
    archivo: Path,
    *,
    nombre_visible: str | None = None,
) -> str:
    """Carga un archivo después de comprobar que existe de forma local."""
    if not archivo.is_file():
        raise ValueError(f"No existe el archivo indicado: {archivo}")

    operacion = cliente.file_search_stores.upload_to_file_search_store(
        file=str(archivo),
        file_search_store_name=almacen,
        config={"display_name": nombre_visible or archivo.name},
    )
    while not getattr(operacion, "done", False):
        time.sleep(2)
        operacion = cliente.operations.get(operacion)
    return str(getattr(operacion, "name", "carga_completada"))


def listar_documentos(cliente: ClienteAdministradorFileSearch, almacen: str) -> list[dict[str, str]]:
    """Devuelve identificadores y nombres sin incluir el contenido de las fuentes."""
    documentos = cliente.file_search_stores.documents.list(parent=almacen)
    return [
        {
            "identificador": str(getattr(documento, "name", "")),
            "nombre_visible": str(getattr(documento, "display_name", "")),
        }
        for documento in documentos
    ]


def main() -> None:
    """Ejecuta una acción administrativa elegida explícitamente por la persona usuaria."""
    argumentos = _crear_argumentos().parse_args()
    cliente = _crear_cliente_desde_entorno()
    if argumentos.accion == "crear-almacen":
        resultado: object = {"almacen": crear_almacen(cliente, argumentos.nombre)}
    elif argumentos.accion == "cargar-archivo":
        resultado = {
            "operacion": cargar_archivo(
                cliente,
                argumentos.almacen,
                Path(argumentos.archivo),
                nombre_visible=argumentos.nombre_visible,
            )
        }
    else:
        resultado = {"documentos": listar_documentos(cliente, argumentos.almacen)}
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


def _crear_argumentos() -> argparse.ArgumentParser:
    """Construye las acciones disponibles sin ofrecer eliminación automática."""
    parser = argparse.ArgumentParser(description="Administrar Gemini File Search.")
    subcomandos = parser.add_subparsers(dest="accion", required=True)

    crear = subcomandos.add_parser("crear-almacen")
    crear.add_argument("--nombre", required=True)

    cargar = subcomandos.add_parser("cargar-archivo")
    cargar.add_argument("--almacen", required=True)
    cargar.add_argument("--archivo", required=True)
    cargar.add_argument("--nombre-visible")

    listar = subcomandos.add_parser("listar-documentos")
    listar.add_argument("--almacen", required=True)
    return parser


def _crear_cliente_desde_entorno() -> ClienteAdministradorFileSearch:
    """Crea el cliente con la clave local sin imprimirla ni almacenarla."""
    clave_api = os.getenv("CLAVE_API_IA", "").strip()
    if not clave_api:
        raise ValueError("CLAVE_API_IA debe configurarse en el archivo .env local.")

    from google import genai

    return genai.Client(api_key=clave_api)


if __name__ == "__main__":
    main()
