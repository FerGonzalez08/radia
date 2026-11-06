"""Configuración de pruebas del servicio de autenticación.

Las pruebas usan una base PostgreSQL real (la misma familia que producción) y NUNCA la de desarrollo
ni la de Azure: la URL se toma de TEST_DATABASE_URL y se aborta si el nombre de la base no contiene «test».
Las variables de entorno se fijan antes de importar la aplicación porque `Settings` se lee al importar.
"""
import os
import uuid
from datetime import date, datetime, timedelta, timezone

TEST_DB = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/radia_test")
if "test" not in TEST_DB.rsplit("/", 1)[-1].lower():
    raise RuntimeError("TEST_DATABASE_URL debe apuntar a una base cuyo nombre contenga 'test' (las pruebas la vacían).")

os.environ.update({
    "DATABASE_URL": TEST_DB,
    "JWT_SECRET_KEY": "clave-solo-para-pruebas",
    "RESEND_API_KEY": "re_test",
    "RESEND_SENDER_EMAIL": "no-reply@pruebas.com",
    "FRONTEND_URL": "http://frontend.test",
    "INTERNAL_SERVICE_KEY": "clave-interna-pruebas",
    "FRONTEND_ORIGINS": "http://localhost:5173",
})

import bcrypt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core import security  # noqa: E402
from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import login_attempt, refresh_token, user, verification_token  # noqa: E402,F401
from app.models.refresh_token import RefreshToken  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.verification_token import VerificationToken  # noqa: E402

PASSWORD = "Contrasena-Segura-1"


@pytest.fixture(scope="session", autouse=True)
def _fast_bcrypt():
    """Reduce el costo de bcrypt solo en pruebas; el algoritmo y el pre-hash SHA-256 no cambian."""
    original = bcrypt.gensalt
    security.bcrypt.gensalt = lambda rounds=4, prefix=b"2b": original(rounds=4, prefix=prefix)
    yield
    security.bcrypt.gensalt = original


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_db():
    with engine.begin() as conn:
        tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sent_emails(monkeypatch):
    """Intercepta los envíos de correo para no salir a la red y poder inspeccionar el token enviado."""
    sent = []
    from app.routers import auth as auth_router
    monkeypatch.setattr(auth_router, "send_verification_email", lambda to, token: sent.append(("verify", to, token)))
    monkeypatch.setattr(auth_router, "send_password_reset_email", lambda to, token: sent.append(("reset", to, token)))
    return sent


@pytest.fixture
def make_user(db):
    def _make(email="ana@pruebas.com", password=PASSWORD, role_id=MENTEE_ROLE_ID, verified=True, active=True,
              birth=date(2000, 1, 1)):
        u = User(
            email=email, password_hash=security.hash_password(password), nombre="Ana Prueba", telefono="3000000000",
            sexo="F", fecha_nacimiento=birth, role_id=role_id, is_verified=verified, is_active=active,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u
    return _make


@pytest.fixture
def make_admin(make_user):
    return lambda email="admin@pruebas.com": make_user(email=email, role_id=ADMIN_ROLE_ID)


@pytest.fixture
def make_token_record(db):
    def _make(user_id, plain, type_="email_verification", expires_in=timedelta(hours=1), used=False):
        rec = VerificationToken(
            user_id=user_id, token_hash=security.hash_opaque_token(plain), type=type_,
            expires_at=datetime.now(timezone.utc) + expires_in,
            used_at=datetime.now(timezone.utc) if used else None,
        )
        db.add(rec)
        db.commit()
        return rec
    return _make


@pytest.fixture
def auth_header():
    def _h(user):
        return {"Authorization": f"Bearer {security.create_access_token(str(user.id), str(user.role_id))}"}
    return _h


def login(client, email="ana@pruebas.com", password=PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})
