"""TC-SEG-17: los registros de seguridad vencidos se depuran con un plazo de retención definido (30 días)."""
from datetime import datetime, timedelta, timezone

from app.core.retention import purge_expired
from app.models.login_attempt import LoginAttempt
from app.models.refresh_token import RefreshToken
from app.models.verification_token import VerificationToken
import uuid

AHORA = datetime.now(timezone.utc)


def test_se_borran_solo_los_registros_que_pasaron_el_plazo_de_retencion(db, make_user):
    u = make_user()
    for dias_vencido, hash_ in ((45, "viejo"), (5, "reciente")):
        db.add(VerificationToken(user_id=u.id, token_hash=hash_, type="password_reset", expires_at=AHORA - timedelta(days=dias_vencido)))
        db.add(RefreshToken(user_id=u.id, token_hash=hash_, family_id=uuid.uuid4(), expires_at=AHORA - timedelta(days=dias_vencido)))
    db.add(VerificationToken(user_id=u.id, token_hash="vigente", type="email_verification", expires_at=AHORA + timedelta(hours=1)))
    db.add_all([
        LoginAttempt(user_id=u.id, email=u.email, ip_address="1.1.1.1", success=False, created_at=AHORA - timedelta(days=40)),
        LoginAttempt(user_id=u.id, email=u.email, ip_address="1.1.1.1", success=False, created_at=AHORA - timedelta(minutes=5)),
    ])
    db.commit()

    borrados = purge_expired(db)

    assert borrados == {"verification_tokens": 1, "refresh_tokens": 1, "login_attempts": 1}
    assert {t.token_hash for t in db.query(VerificationToken).all()} == {"reciente", "vigente"}
    assert [t.token_hash for t in db.query(RefreshToken).all()] == ["reciente"]
    assert db.query(LoginAttempt).count() == 1
    assert purge_expired(db) == {"verification_tokens": 0, "refresh_tokens": 0, "login_attempts": 0}  # idempotente
