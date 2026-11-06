"""Catálogo de categorías (RQF-024), categorías de la mentora (RQF-031) y búsqueda de mentoras (RQF-027)."""
import uuid

from app.models.mentor_category import MentorCategory


def test_crear_categoria_y_listarla_ordenada(client, admin, mentee):
    assert client.post("/categories", json={"name": "Zeta"}, headers=admin.headers).status_code == 201
    assert client.post("/categories", json={"name": "Alfa", "description": "d"}, headers=admin.headers).status_code == 201
    nombres = [c["name"] for c in client.get("/categories", headers=mentee.headers).json()]
    assert nombres == ["Alfa", "Zeta"]


def test_crear_categoria_duplicada_o_invalida(client, admin, make_category):
    make_category("Python")
    assert client.post("/categories", json={"name": "Python"}, headers=admin.headers).status_code == 409
    assert client.post("/categories", json={"name": ""}, headers=admin.headers).status_code == 422
    assert client.post("/categories", json={"name": "x" * 101}, headers=admin.headers).status_code == 422


def test_actualizar_categoria(client, admin, make_category):
    c = make_category("Python")
    r = client.put(f"/categories/{c.id}", json={"name": "Python 3", "description": "nueva"}, headers=admin.headers)
    assert r.status_code == 200 and r.json()["name"] == "Python 3" and r.json()["description"] == "nueva"


def test_actualizar_categoria_con_nombre_ya_usado_o_inexistente(client, admin, make_category):
    make_category("Python")
    otra = make_category("Java")
    assert client.put(f"/categories/{otra.id}", json={"name": "Python"}, headers=admin.headers).status_code == 409
    assert client.put(f"/categories/{uuid.uuid4()}", json={"name": "X"}, headers=admin.headers).status_code == 404


def test_actualizar_con_el_mismo_nombre_no_es_conflicto(client, admin, make_category):
    c = make_category("Python")
    assert client.put(f"/categories/{c.id}", json={"name": "Python", "description": "x"}, headers=admin.headers).status_code == 200


def test_eliminar_categoria_libre(client, admin, make_category):
    c = make_category("Python")
    assert client.delete(f"/categories/{c.id}", headers=admin.headers).status_code == 204
    assert client.delete(f"/categories/{c.id}", headers=admin.headers).status_code == 404


def test_no_se_elimina_una_categoria_en_uso(client, db, admin, mentor, make_category):
    c = make_category("Python")
    db.add(MentorCategory(mentor_user_id=mentor.id, category_id=c.id))
    db.commit()
    assert client.delete(f"/categories/{c.id}", headers=admin.headers).status_code == 409


def test_la_mentora_reemplaza_su_conjunto_de_categorias(client, mentor, make_category):
    a, b, c = make_category("A"), make_category("B"), make_category("C")
    r = client.put("/mentors/me/categories", json={"category_ids": [str(a.id), str(b.id)]}, headers=mentor.headers)
    assert r.status_code == 200 and {x["name"] for x in r.json()} == {"A", "B"}
    client.put("/mentors/me/categories", json={"category_ids": [str(c.id)]}, headers=mentor.headers)
    assert [x["name"] for x in client.get("/mentors/me/categories", headers=mentor.headers).json()] == ["C"]


def test_la_mentora_no_puede_elegir_categorias_inexistentes(client, mentor, make_category):
    a = make_category("A")
    r = client.put("/mentors/me/categories", json={"category_ids": [str(a.id), str(uuid.uuid4())]}, headers=mentor.headers)
    assert r.status_code == 400
    assert client.get("/mentors/me/categories", headers=mentor.headers).json() == []


def test_las_categorias_de_una_mentora_no_afectan_a_otra(client, mentor, mentor2, make_category):
    a = make_category("A")
    client.put("/mentors/me/categories", json={"category_ids": [str(a.id)]}, headers=mentor.headers)
    assert client.get("/mentors/me/categories", headers=mentor2.headers).json() == []


def test_buscar_mentoras_por_categoria(client, fake_auth, mentee, mentor, mentor2, make_category):
    py, js = make_category("Python"), make_category("JS")
    client.put("/mentors/me/categories", json={"category_ids": [str(py.id), str(js.id)]}, headers=mentor.headers)
    client.put("/mentors/me/categories", json={"category_ids": [str(js.id)]}, headers=mentor2.headers)
    r = client.get("/search/mentors", params={"category_id": str(py.id)}, headers=mentee.headers)
    assert r.status_code == 200
    assert [m["nombre"] for m in r.json()] == ["Mentora Uno"]
    assert sorted(r.json()[0]["categories"]) == ["JS", "Python"]
    assert len(client.get("/search/mentors", params={"category_id": str(js.id)}, headers=mentee.headers).json()) == 2


def test_buscar_sin_resultados_no_consulta_a_auth(client, monkeypatch, mentee, make_category):
    from app.routers import categories

    async def no_debe_llamarse():
        raise AssertionError("no debía consultar la lista de usuarios")
    monkeypatch.setattr(categories, "list_users_internal", no_debe_llamarse)
    c = make_category("Vacia")
    assert client.get("/search/mentors", params={"category_id": str(c.id)}, headers=mentee.headers).json() == []


def test_la_busqueda_excluye_a_quien_ya_no_es_mentora(client, fake_auth, mentee, mentor, make_category):
    from app.core.config import MENTEE_ROLE_ID
    c = make_category("Python")
    client.put("/mentors/me/categories", json={"category_ids": [str(c.id)]}, headers=mentor.headers)
    fake_auth.users[mentor.user["id"]]["role_id"] = str(MENTEE_ROLE_ID)  # revertida por el administrador
    assert client.get("/search/mentors", params={"category_id": str(c.id)}, headers=mentee.headers).json() == []


def test_buscar_exige_category_id_valido(client, mentee):
    assert client.get("/search/mentors", headers=mentee.headers).status_code == 422
    assert client.get("/search/mentors", params={"category_id": "x"}, headers=mentee.headers).status_code == 422
