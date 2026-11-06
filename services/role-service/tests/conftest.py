"""Configuración de pruebas del servicio de roles.

Role Service no valida sesiones por su cuenta: le pregunta a Auth Service por HTTP. En las pruebas, ese servicio se
sustituye por un doble en memoria (httpx.MockTransport) que responde lo mismo que respondería el real, de modo que se
prueba la lógica de roles de este servicio y su contrato con Auth, no la red.
"""
import os
import uuid

TEST_DB = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/radia_test")
if "test" not in TEST_DB.rsplit("/", 1)[-1].lower():
    raise RuntimeError("TEST_DATABASE_URL debe apuntar a una base cuyo nombre contenga 'test' (las pruebas la vacían).")

os.environ.update({
    "DATABASE_URL": TEST_DB,
    "AUTH_SERVICE_URL": "http://auth.test",
    "INTERNAL_SERVICE_KEY": "clave-interna-pruebas",
    "FRONTEND_ORIGINS": "http://localhost:5173",
})

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core import auth_client  # noqa: E402
from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.role_change_log import RoleChangeLog  # noqa: E402,F401


class FakeAuth:
    """Doble en memoria de Auth Service: sesiones por token y lista de usuarios."""

    def __init__(self):
        self.users: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.down = False
        self.role_updates: list[tuple[str, str]] = []

    def add_user(self, role_id, nombre="Persona", email=None, active=True, verified=True) -> dict:
        uid = str(uuid.uuid4())
        user = {"id": uid, "email": email or f"{uid[:8]}@pruebas.com", "nombre": nombre, "role_id": str(role_id),
                "is_verified": verified, "is_active": active}
        self.users[uid] = user
        return user

    def login_as(self, user: dict) -> dict:
        token = f"tok-{user['id']}"
        self.sessions[token] = {"valid": True, "user_id": user["id"], "role_id": user["role_id"]}
        return {"Authorization": f"Bearer {token}"}

    def handler(self, request: httpx.Request) -> httpx.Response:
        if self.down:
            return httpx.Response(503, json={"detail": "down"})
        path = request.url.path
        if path == "/auth/validate-session":
            token = request.headers.get("authorization", "").removeprefix("Bearer ")
            session = self.sessions.get(token)
            return httpx.Response(200, json=session) if session else httpx.Response(401, json={"detail": "x"})
        if request.headers.get("x-internal-service-key") != "clave-interna-pruebas":
            return httpx.Response(403, json={"detail": "Invalid internal service key"})
        if path == "/internal/users" and request.method == "GET":
            return httpx.Response(200, json=list(self.users.values()))
        if path.startswith("/internal/users/") and path.endswith("/role") and request.method == "PATCH":
            uid = path.split("/")[3]
            if uid not in self.users:
                return httpx.Response(404, json={"detail": "Usuario no encontrado"})
            import json
            role_id = json.loads(request.content)["role_id"]
            self.users[uid]["role_id"] = role_id
            self.role_updates.append((uid, role_id))
            return httpx.Response(200, json=self.users[uid])
        return httpx.Response(404)


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
        for rid, name in ((MENTEE_ROLE_ID, "estudiante"), (MENTOR_ROLE_ID, "mentora"), (ADMIN_ROLE_ID, "administrador")):
            conn.execute(text("INSERT INTO roles (id, name, description) VALUES (:i, :n, :d)"),
                         {"i": rid, "n": name, "d": f"rol {name}"})
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def fake_auth(monkeypatch):
    fake = FakeAuth()
    real_client = httpx.AsyncClient
    monkeypatch.setattr(auth_client.httpx, "AsyncClient",
                        lambda *a, **kw: real_client(transport=httpx.MockTransport(fake.handler)))
    return fake


@pytest.fixture
def client(fake_auth):
    return TestClient(app)


@pytest.fixture
def admin(fake_auth):
    user = fake_auth.add_user(ADMIN_ROLE_ID, nombre="Admin Uno")
    return user, fake_auth.login_as(user)
