"""Promoción a mentora, reversión a estudiante y bitácora de auditoría (RQF-007/008, HU-AUDIT)."""
import uuid

from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID
from app.models.role_change_log import RoleChangeLog


def test_promover_estudiante_a_mentora_actualiza_auth_y_registra_la_bitacora(client, db, fake_auth, admin):
    adm, headers = admin
    ana = fake_auth.add_user(MENTEE_ROLE_ID, nombre="Ana")
    r = client.post(f"/roles/{ana['id']}/promote", headers=headers)
    assert r.status_code == 200 and r.json()["role_id"] == str(MENTOR_ROLE_ID)
    assert fake_auth.role_updates == [(ana["id"], str(MENTOR_ROLE_ID))]
    log = db.query(RoleChangeLog).one()
    assert str(log.target_user_id) == ana["id"] and str(log.admin_user_id) == adm["id"]
    assert log.previous_role_id == MENTEE_ROLE_ID and log.new_role_id == MENTOR_ROLE_ID


def test_promover_a_quien_ya_es_mentora_responde_400_y_no_registra(client, db, fake_auth, admin):
    _, headers = admin
    m = fake_auth.add_user(MENTOR_ROLE_ID)
    assert client.post(f"/roles/{m['id']}/promote", headers=headers).status_code == 400
    assert db.query(RoleChangeLog).count() == 0 and fake_auth.role_updates == []


def test_no_se_puede_reasignar_el_rol_de_un_administrador(client, db, fake_auth, admin):
    _, headers = admin
    otro = fake_auth.add_user(ADMIN_ROLE_ID, nombre="Otro Admin")
    assert client.post(f"/roles/{otro['id']}/promote", headers=headers).status_code == 409
    assert client.post(f"/roles/{otro['id']}/revert", headers=headers).status_code == 409
    assert db.query(RoleChangeLog).count() == 0 and fake_auth.role_updates == []


def test_promover_usuario_inexistente_responde_404(client, admin):
    _, headers = admin
    assert client.post(f"/roles/{uuid.uuid4()}/promote", headers=headers).status_code == 404
    assert client.post(f"/roles/{uuid.uuid4()}/revert", headers=headers).status_code == 404


def test_id_con_formato_invalido_responde_422(client, admin):
    _, headers = admin
    assert client.post("/roles/no-es-uuid/promote", headers=headers).status_code == 422


def test_revertir_mentora_a_estudiante(client, db, fake_auth, admin):
    _, headers = admin
    m = fake_auth.add_user(MENTOR_ROLE_ID)
    r = client.post(f"/roles/{m['id']}/revert", headers=headers)
    assert r.status_code == 200 and r.json()["role_id"] == str(MENTEE_ROLE_ID)
    log = db.query(RoleChangeLog).one()
    assert log.previous_role_id == MENTOR_ROLE_ID and log.new_role_id == MENTEE_ROLE_ID


def test_revertir_a_quien_no_es_mentora_responde_400(client, db, fake_auth, admin):
    _, headers = admin
    e = fake_auth.add_user(MENTEE_ROLE_ID)
    assert client.post(f"/roles/{e['id']}/revert", headers=headers).status_code == 400
    assert db.query(RoleChangeLog).count() == 0


def test_promover_y_revertir_dejan_dos_entradas_en_orden(client, fake_auth, admin):
    _, headers = admin
    ana = fake_auth.add_user(MENTEE_ROLE_ID, nombre="Ana")
    client.post(f"/roles/{ana['id']}/promote", headers=headers)
    client.post(f"/roles/{ana['id']}/revert", headers=headers)
    log = client.get("/roles/audit-log", headers=headers).json()
    assert [(e["previous_role"], e["new_role"]) for e in log] == [("mentora", "estudiante"), ("estudiante", "mentora")]


def test_si_auth_falla_al_actualizar_no_se_registra_el_cambio(client, db, fake_auth, admin, monkeypatch):
    from app.routers import roles as roles_router
    from fastapi import HTTPException
    _, headers = admin
    ana = fake_auth.add_user(MENTEE_ROLE_ID)

    async def falla(user_id, role_id):
        raise HTTPException(502, "Auth Service unavailable")
    monkeypatch.setattr(roles_router, "update_user_role_internal", falla)
    assert client.post(f"/roles/{ana['id']}/promote", headers=headers).status_code == 502
    assert db.query(RoleChangeLog).count() == 0


def test_bitacora_vacia(client, admin):
    _, headers = admin
    assert client.get("/roles/audit-log", headers=headers).json() == []


def test_bitacora_resuelve_nombres_correos_y_roles(client, fake_auth, admin):
    adm, headers = admin
    ana = fake_auth.add_user(MENTEE_ROLE_ID, nombre="Ana", email="ana@pruebas.com")
    client.post(f"/roles/{ana['id']}/promote", headers=headers)
    entry = client.get("/roles/audit-log", headers=headers).json()[0]
    assert entry["admin_nombre"] == "Admin Uno" and entry["admin_email"] == adm["email"]
    assert entry["target_nombre"] == "Ana" and entry["target_email"] == "ana@pruebas.com"
    assert (entry["previous_role"], entry["new_role"]) == ("estudiante", "mentora")


def test_bitacora_marca_usuarios_eliminados(client, fake_auth, admin):
    _, headers = admin
    ana = fake_auth.add_user(MENTEE_ROLE_ID, nombre="Ana")
    client.post(f"/roles/{ana['id']}/promote", headers=headers)
    del fake_auth.users[ana["id"]]
    entry = client.get("/roles/audit-log", headers=headers).json()[0]
    assert entry["target_nombre"] == "Usuario eliminado" and entry["target_email"] == "-"


def test_bitacora_con_rol_fuera_de_catalogo_dice_desconocido(client, db, fake_auth, admin):
    adm, headers = admin
    ana = fake_auth.add_user(MENTEE_ROLE_ID)
    client.post(f"/roles/{ana['id']}/promote", headers=headers)
    db.execute(__import__("sqlalchemy").text("ALTER TABLE role_change_log DROP CONSTRAINT IF EXISTS role_change_log_new_role_id_fkey"))
    db.execute(__import__("sqlalchemy").text("UPDATE role_change_log SET new_role_id = :x"), {"x": str(uuid.uuid4())})
    db.commit()
    assert client.get("/roles/audit-log", headers=headers).json()[0]["new_role"] == "Desconocido"
