import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# --- Password hashing ---
# Pre-hash con SHA-256 antes de bcrypt: bcrypt trunca en 72 bytes,
# esto evita ese límite silencioso en contraseñas largas.

def hash_password(plain_password: str) -> str:
    prehashed = hashlib.sha256(plain_password.encode("utf-8")).digest()
    return bcrypt.hashpw(prehashed, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    prehashed = hashlib.sha256(plain_password.encode("utf-8")).digest()
    return bcrypt.checkpw(prehashed, hashed_password.encode("utf-8"))


# --- Access token (JWT, HS256) ---

def create_access_token(user_id: str, role_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role_id": role_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


# --- Opaque tokens (refresh token, verification token) ---
# No son JWT: son un valor aleatorio que se entrega al cliente,
# y en la base de datos solo se guarda su hash (nunca el token plano).

def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
