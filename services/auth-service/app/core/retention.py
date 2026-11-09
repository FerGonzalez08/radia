"""Retención y depuración de datos de seguridad vencidos (TC-SEG-17).

Plazo de retención (RETENTION_DAYS, 30 días por defecto) contado desde el vencimiento o la creación:
- Tokens de verificación y de restablecimiento: se borran 30 días después de vencer.
- Refresh tokens: se borran 30 días después de vencer (los revocados siguen su vencimiento original).
- Intentos de inicio de sesión: se borran 30 días después de registrarse; el bloqueo solo mira los últimos 10 minutos.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.login_attempt import LoginAttempt
from app.models.refresh_token import RefreshToken
from app.models.verification_token import VerificationToken

logger = logging.getLogger(__name__)


def purge_expired(db: Session, now: datetime | None = None) -> dict[str, int]:
    """Borra los registros cuyo plazo de retención ya pasó. Es idempotente. Devuelve cuántos borró por tabla."""
    limite = (now or datetime.now(timezone.utc)) - timedelta(days=settings.RETENTION_DAYS)
    borrados = {
        "verification_tokens": db.query(VerificationToken).filter(VerificationToken.expires_at < limite).delete(synchronize_session=False),
        "refresh_tokens": db.query(RefreshToken).filter(RefreshToken.expires_at < limite).delete(synchronize_session=False),
        "login_attempts": db.query(LoginAttempt).filter(LoginAttempt.created_at < limite).delete(synchronize_session=False),
    }
    db.commit()
    return borrados


def _purge_once() -> None:
    db = SessionLocal()
    try:
        borrados = purge_expired(db)
        logger.info("Depuración de datos vencidos: %s", borrados)
    except Exception:
        logger.exception("Falló la depuración de datos vencidos")
        db.rollback()
    finally:
        db.close()


async def purge_loop() -> None:
    """Depura al arrancar y luego cada PURGE_INTERVAL_HOURS horas (0 desactiva la tarea)."""
    if settings.PURGE_INTERVAL_HOURS <= 0:
        return
    while True:
        await asyncio.get_running_loop().run_in_executor(None, _purge_once)
        await asyncio.sleep(settings.PURGE_INTERVAL_HOURS * 3600)
