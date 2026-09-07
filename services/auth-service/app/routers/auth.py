import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.email import send_password_reset_email, send_verification_email
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.models.login_attempt import LoginAttempt
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.verification_token import VerificationToken
from app.schemas.token import RefreshRequest, TokenPair, ValidateSessionResponse
from app.schemas.user import UserLogin, UserOut, UserRegister
from app.schemas.verification import (
    PasswordResetConfirm,
    PasswordResetRequest,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _issue_token_pair(db: Session, user: User) -> TokenPair:
    access_token = create_access_token(str(user.id), str(user.role_id))

    refresh_plain = generate_opaque_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_opaque_token(refresh_plain),
        family_id=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_token)
    db.commit()

    return TokenPair(access_token=access_token, refresh_token=refresh_plain)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=payload.role_id,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    verification_plain = generate_opaque_token()
    verification = VerificationToken(
        user_id=user.id,
        token_hash=hash_opaque_token(verification_plain),
        type="email_verification",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verification)
    db.commit()

    send_verification_email(user.email, verification_plain)

    return user


@router.post("/login", response_model=TokenPair)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    ip_address = _get_client_ip(request)
    user = db.query(User).filter(User.email == payload.email).first()

    success = user is not None and verify_password(payload.password, user.password_hash)

    db.add(LoginAttempt(
        user_id=user.id if user else None,
        email=payload.email,
        ip_address=ip_address,
        success=bool(success),
    ))
    db.commit()

    if not success:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated")

    if not user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email not verified")

    return _issue_token_pair(db, user)


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_opaque_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if stored is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    if stored.revoked_at is not None:
        # Reuso de un token ya revocado: revoca toda la familia (posible robo de token).
        db.query(RefreshToken).filter(
            RefreshToken.family_id == stored.family_id,
            RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": datetime.now(timezone.utc)})
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token reuse detected")

    if stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    user = db.query(User).filter(User.id == stored.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    # Rotación: se revoca el token usado y se emite uno nuevo en la misma familia.
    stored.revoked_at = datetime.now(timezone.utc)

    access_token = create_access_token(str(user.id), str(user.role_id))
    new_plain = generate_opaque_token()
    new_refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_opaque_token(new_plain),
        family_id=stored.family_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_refresh)
    db.commit()

    return TokenPair(access_token=access_token, refresh_token=new_plain)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_opaque_token(payload.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if stored is not None:
        db.query(RefreshToken).filter(
            RefreshToken.family_id == stored.family_id,
            RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": datetime.now(timezone.utc)})
        db.commit()

    return None


@router.get("/validate-session", response_model=ValidateSessionResponse)
def validate_session(current_user: User = Depends(get_current_user)):
    # get_current_user ya valida firma, expiración, existencia y is_active.
    # Este endpoint es el único punto de verdad que otros microservicios consultan.
    return ValidateSessionResponse(
        valid=True,
        user_id=current_user.id,
        role_id=current_user.role_id,
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    token_hash = hash_opaque_token(payload.token)
    record = db.query(VerificationToken).filter(
        VerificationToken.token_hash == token_hash,
        VerificationToken.type == "email_verification",
    ).first()

    if record is None or record.used_at is not None or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired verification token")

    user = db.query(User).filter(User.id == record.user_id).first()
    user.is_verified = True
    record.used_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if user is not None:
        reset_plain = generate_opaque_token()
        db.add(VerificationToken(
            user_id=user.id,
            token_hash=hash_opaque_token(reset_plain),
            type="password_reset",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))
        db.commit()
        send_password_reset_email(user.email, reset_plain)

    # Responde 204 exista o no el email — evita filtrar qué correos están registrados.
    return None


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_hash = hash_opaque_token(payload.token)
    record = db.query(VerificationToken).filter(
        VerificationToken.token_hash == token_hash,
        VerificationToken.type == "password_reset",
    ).first()

    if record is None or record.used_at is not None or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")

    user = db.query(User).filter(User.id == record.user_id).first()
    user.password_hash = hash_password(payload.new_password)
    record.used_at = datetime.now(timezone.utc)

    # Al resetear contraseña, se revocan todas las sesiones activas del usuario.
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": datetime.now(timezone.utc)})

    db.commit()
    return None
