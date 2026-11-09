"""TC-NFR-10: cada respuesta lleva X-Request-ID para correlacionar una operación entre servicios."""
from app.core.request_id import HEADER


def test_la_respuesta_trae_un_identificador_generado(client):
    r = client.get("/health")
    assert r.status_code == 200 and len(r.headers[HEADER]) == 32


def test_se_conserva_el_identificador_que_envia_el_cliente(client):
    r = client.get("/health", headers={HEADER: "abc-12345-correlacion"})
    assert r.headers[HEADER] == "abc-12345-correlacion"


def test_un_identificador_invalido_se_reemplaza(client):
    r = client.get("/health", headers={HEADER: "<script>alert(1)</script>"})
    assert r.headers[HEADER] != "<script>alert(1)</script>" and len(r.headers[HEADER]) == 32


def test_tambien_se_devuelve_en_errores(client):
    r = client.get("/ruta-que-no-existe")
    assert r.status_code == 404 and HEADER in r.headers
