"""Configuración de pruebas del servicio de chat.

Auth Service y Navigation Service se sustituyen por un doble en memoria (httpx.MockTransport). La base es PostgreSQL real.
Los WebSockets se prueban con el cliente de Starlette, que ejecuta el mismo código de aplicación que Uvicorn.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

TEST_DB = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/radia_test")
if "test" not in TEST_DB.rsplit("/", 1)[-1].lower():
    raise RuntimeError("TEST_DATABASE_URL debe apuntar a una base cuyo nombre contenga 'test' (las pruebas la vacían).")

os.environ.update({
    "DATABASE_URL": TEST_DB,
    "AUTH_SERVICE_URL": "http://auth.test",
    "NAVIGATION_SERVICE_URL": "http://nav.test",
    "INTERNAL_SERVICE_KEY": "clave-interna-pruebas",
    "FRONTEND_ORIGINS": "http://localhost:5173",
})

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core import clients  # noqa: E402
from app.core.config import MENTEE_ROLE_ID, MENTOR_ROLE_ID  # noqa: E402
from app.core.connection_manager import manager  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import conversation, last_seen, message  # noqa: E402,F401
from app.models.conversation import Conversation  # noqa: E402
from app.models.message import Message  # noqa: E402


class FakeAuth:
    """Doble en memoria de Auth Service: sesiones por token y lista de usuarios."""

    def __init__(self):
        self.users: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.down = False
        self.nav_down = False
        self.mentorships: set[frozenset] = set()
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
        if request.url.host == "nav.test":
            if request.headers.get("x-internal-service-key") != "clave-interna-pruebas":
                return httpx.Response(403)
            if self.nav_down:
                return httpx.Response(503)
            a, b = request.url.params["user_a"], request.url.params["user_b"]
            return httpx.Response(200, json={"active": frozenset((a, b)) in self.mentorships})
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
    manager.active_connections.clear()
    with engine.begin() as conn:
        tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield
    manager.active_connections.clear()


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
    monkeypatch.setattr(clients.httpx, "AsyncClient",
                        lambda *a, **kw: real_client(transport=httpx.MockTransport(fake.handler)))
    return fake


@pytest.fixture
def client(fake_auth):
    return TestClient(app)


class Persona:
    def __init__(self, user, headers):
        self.user, self.headers = user, headers
        self.id = uuid.UUID(user["id"])
        self.token = headers["Authorization"].removeprefix("Bearer ")


@pytest.fixture
def mentee(fake_auth):
    u = fake_auth.add_user(MENTEE_ROLE_ID, nombre="Estudiante Uno")
    return Persona(u, fake_auth.login_as(u))


@pytest.fixture
def mentor(fake_auth):
    u = fake_auth.add_user(MENTOR_ROLE_ID, nombre="Mentora Uno")
    return Persona(u, fake_auth.login_as(u))


@pytest.fixture
def otra_mentora(fake_auth):
    u = fake_auth.add_user(MENTOR_ROLE_ID, nombre="Mentora Dos")
    return Persona(u, fake_auth.login_as(u))


@pytest.fixture
def vinculo(fake_auth, mentee, mentor):
    """Mentoría activa entre mentee y mentor (lo que Navigation Service respondería como «active: true»)."""
    fake_auth.mentorships.add(frozenset((str(mentee.id), str(mentor.id))))


@pytest.fixture
def conversacion(db, mentee, mentor):
    c = Conversation(student_user_id=mentee.id, mentor_user_id=mentor.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def make_message(db, conversacion):
    base = datetime(2030, 1, 7, 12, 0, tzinfo=timezone.utc)
    contador = {"n": 0}

    def _make(sender, content="hola", read=False):
        contador["n"] += 1
        m = Message(conversation_id=conversacion.id, sender_user_id=sender.id, content=content,
                    created_at=base + timedelta(minutes=contador["n"]),
                    read_at=base if read else None)
        db.add(m)
        db.commit()
        db.refresh(m)
        return m
    return _make
