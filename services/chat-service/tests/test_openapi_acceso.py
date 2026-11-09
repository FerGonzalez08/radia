"""TC-DOC-01: cada endpoint documenta en Swagger quién puede usarlo."""
from app.main import app


def test_todos_los_endpoints_documentan_el_acceso():
    sin_acceso = []
    for path, ops in app.openapi()["paths"].items():
        for metodo, op in ops.items():
            if metodo in ("get", "post", "put", "patch", "delete") and "Acceso:" not in (op.get("description") or ""):
                sin_acceso.append(f"{metodo.upper()} {path}")
    assert sin_acceso == []
