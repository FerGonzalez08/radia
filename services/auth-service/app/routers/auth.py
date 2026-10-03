import uuid
from datetime import datetime, timedelta, timezone, date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID, settings
from app.core.deps import get_current_user, require_admin
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
from app.schemas.user import RoleUpdateRequest, UserLogin, UserOut, UserRegister
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

def _calculate_age(birth_date: date) -> int:
    today = datetime.now(timezone.utc).date()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese correo ya está registrado")

    if _calculate_age(payload.fecha_nacimiento) < 18:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se permite el registro de usuarios menores de edad",
        )
    
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nombre=payload.nombre,
        telefono=payload.telefono,
        sexo=payload.sexo,
        fecha_nacimiento=payload.fecha_nacimiento,
        role_id=MENTEE_ROLE_ID,
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

    try:
        send_verification_email(user.email, verification_plain)
    except Exception:
        # El registro no debe fallar si el envío de correo falla — el usuario
        # ya quedó creado; la verificación puede reintentarse o hacerse manual.
        pass

    return user

def _check_login_lockout(db: Session, email: str) -> datetime | None:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=10)

    failed_count = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.success.is_(False),
        LoginAttempt.created_at >= window_start,
    ).count()

    if failed_count < 5:
        return None

    last_failed = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.success.is_(False),
    ).order_by(LoginAttempt.created_at.desc()).first()

    unlock_at = last_failed.created_at + timedelta(minutes=15)
    return unlock_at if now < unlock_at else None

@router.post("/login", response_model=TokenPair)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    ip_address = _get_client_ip(request)

    unlock_at = _check_login_lockout(db, payload.email)
    if unlock_at is not None:
        remaining_minutes = max(1, int((unlock_at - datetime.now(timezone.utc)).total_seconds() // 60) + 1)
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Demasiados intentos fallidos. Intenta de nuevo en {remaining_minutes} minuto(s).",
        )
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
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
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

@router.get("/admin/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/admin/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: uuid.UUID,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    if target_user.role_id == ADMIN_ROLE_ID:
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede reasignar el rol de un administrador")

    was_mentor = target_user.role_id == MENTOR_ROLE_ID
    target_user.role_id = payload.role_id
    db.commit()
    db.refresh(target_user)

    if was_mentor and payload.role_id != MENTOR_ROLE_ID:
        # TODO: notificar a Navigation Service para cancelar mentorías activas
        # de este usuario. Pendiente de definir: llamada síncrona vs evento
        # asíncrono (ver decisión arquitectónica en RQF-008). No implementado
        # porque Navigation Service no existe todavía.
        pass

    return target_user
