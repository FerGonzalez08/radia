"""Registro y verificación de correo (RQF-001, HU001/HU002)."""
from datetime import date, datetime, timedelta, timezone

from app.core.config import MENTEE_ROLE_ID
from app.core.security import hash_opaque_token
from app.models.user import User
from app.models.verification_token import VerificationToken

PAYLOAD = {
    "email": "nueva@pruebas.com", "password": "Contrasena-Segura-1", "nombre": "Nueva Usuaria",
    "telefono": "3001112233", "sexo": "F", "fecha_nacimiento": "2000-05-20",
}


def test_registro_exitoso_crea_mentee_no_verificada_y_envia_correo(client, db, sent_emails):
    r = client.post("/auth/register", json=PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == PAYLOAD["email"]
    assert body["role_id"] == str(MENTEE_ROLE_ID)
    assert body["is_verified"] is False and body["is_active"] is True
    assert "password" not in body and "password_hash" not in body
    stored = db.query(User).filter(User.email == PAYLOAD["email"]).one()
    assert stored.password_hash != PAYLOAD["password"]
    assert [e[0] for e in sent_emails] == ["verify"] and sent_emails[0][1] == PAYLOAD["email"]


def test_registro_guarda_solo_el_hash_del_token_de_verificacion(client, db, sent_emails):
    client.post("/auth/register", json=PAYLOAD)
    plain = sent_emails[0][2]
    rec = db.query(VerificationToken).one()
    assert rec.token_hash == hash_opaque_token(plain) and rec.token_hash != plain
    assert rec.type == "email_verification"
    assert rec.expires_at > datetime.now(timezone.utc) + timedelta(hours=23)


def test_registro_correo_duplicado_responde_409(client, make_user, sent_emails):
    make_user(email=PAYLOAD["email"])
    assert client.post("/auth/register", json=PAYLOAD).status_code == 409


def test_registro_de_menor_de_edad_se_rechaza(client, db, sent_emails):
    hoy = datetime.now(timezone.utc).date()
    menor = hoy.replace(year=hoy.year - 17)
    r = client.post("/auth/register", json={**PAYLOAD, "fecha_nacimiento": menor.isoformat()})
    assert r.status_code == 400
    assert db.query(User).count() == 0


def test_registro_con_exactamente_18_anios_se_acepta(client, sent_emails):
    hoy = datetime.now(timezone.utc).date()
    r = client.post("/auth/register", json={**PAYLOAD, "fecha_nacimiento": hoy.replace(year=hoy.year - 18).isoformat()})
    assert r.status_code == 201


def test_registro_un_dia_antes_de_cumplir_18_se_rechaza(client, sent_emails):
    hoy = datetime.now(timezone.utc).date()
    casi = (hoy + timedelta(days=1)).replace(year=hoy.year - 18)
    assert client.post("/auth/register", json={**PAYLOAD, "fecha_nacimiento": casi.isoformat()}).status_code == 400


def test_registro_no_falla_si_el_envio_de_correo_falla(client, db, monkeypatch):
    from app.routers import auth as auth_router

    def boom(*a, **k):
        raise RuntimeError("proveedor caído")
    monkeypatch.setattr(auth_router, "send_verification_email", boom)
    assert client.post("/auth/register", json=PAYLOAD).status_code == 201
    assert db.query(User).count() == 1


def test_registro_valida_entradas(client, sent_emails):
    assert client.post("/auth/register", json={**PAYLOAD, "password": "corta"}).status_code == 422
    assert client.post("/auth/register", json={**PAYLOAD, "email": "no-es-correo"}).status_code == 422
    sin_nombre = {k: v for k, v in PAYLOAD.items() if k != "nombre"}
    assert client.post("/auth/register", json=sin_nombre).status_code == 422


def test_verificar_correo_activa_la_cuenta_y_el_token_es_de_un_solo_uso(client, db, make_user, make_token_record):
    u = make_user(verified=False)
    make_token_record(u.id, "tok-1")
    assert client.post("/auth/verify-email", json={"token": "tok-1"}).status_code == 204
    db.expire_all()
    assert db.query(User).filter(User.id == u.id).one().is_verified is True
    assert client.post("/auth/verify-email", json={"token": "tok-1"}).status_code == 400


def test_verificar_correo_con_token_inexistente_o_vencido_o_de_otro_tipo(client, make_user, make_token_record):
    u = make_user(verified=False)
    make_token_record(u.id, "vencido", expires_in=timedelta(seconds=-5))
    make_token_record(u.id, "reset", type_="password_reset")
    assert client.post("/auth/verify-email", json={"token": "no-existe"}).status_code == 400
    assert client.post("/auth/verify-email", json={"token": "vencido"}).status_code == 400
    assert client.post("/auth/verify-email", json={"token": "reset"}).status_code == 400
