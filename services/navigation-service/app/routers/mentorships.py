import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_client import get_user, list_users_internal
from app.core.config import MENTEE_ROLE_ID
from app.core.database import get_db
from app.core.deps import get_current_session, require_mentor
from app.core.email import send_mentorship_confirmation
from app.models.availability_slot import AvailabilitySlot
from app.models.mentor_settings import MentorSettings
from app.models.mentorship import Mentorship
from app.core.internal_auth import verify_internal_key
from app.schemas.mentorship import (
    MentorSettingsOut,
    MentorSettingsUpdate,
    MentorshipOut,
    MentorshipRequestCreate,
)

router = APIRouter(tags=["mentorships"])


def _get_or_create_settings(db: Session, mentor_id: uuid.UUID) -> MentorSettings:
    settings_row = db.query(MentorSettings).filter(MentorSettings.mentor_user_id == mentor_id).first()
    if settings_row is None:
        settings_row = MentorSettings(mentor_user_id=mentor_id, auto_accept=False, weekly_limit=5)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def _lock_settings(db: Session, mentor_id: uuid.UUID) -> MentorSettings:
    """Configuración de la mentora con bloqueo de fila (SELECT ... FOR UPDATE) hasta el commit o rollback.

    Serializa, por mentora, la comprobación del límite semanal y la creación o confirmación de mentorías: sin el bloqueo
    dos solicitudes simultáneas (incluso en instancias distintas) leen el mismo conteo y superan el límite (ASR-27).
    """
    query = db.query(MentorSettings).filter(MentorSettings.mentor_user_id == mentor_id).with_for_update()
    row = query.first()
    if row is None:
        try:
            db.add(MentorSettings(mentor_user_id=mentor_id, auto_accept=False, weekly_limit=5))
            db.commit()
        except IntegrityError:
            db.rollback()  # otra solicitud la creó al mismo tiempo
        row = query.first()
    return row


def _week_bounds(target_date: date) -> tuple[date, date]:
    monday = target_date - timedelta(days=target_date.isoweekday() - 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _confirmed_count_in_week(db: Session, mentor_id: uuid.UUID, target_date: date) -> int:
    monday, sunday = _week_bounds(target_date)
    return (
        db.query(Mentorship)
        .join(AvailabilitySlot, Mentorship.availability_slot_id == AvailabilitySlot.id)
        .filter(
            Mentorship.mentor_user_id == mentor_id,
            Mentorship.status == "confirmada",
            AvailabilitySlot.date >= monday,
            AvailabilitySlot.date <= sunday,
        )
        .count()
    )


async def _send_confirmation_emails(db: Session, mentorship: Mentorship, slot: AvailabilitySlot):
    student = await get_user(str(mentorship.student_user_id))
    mentor = await get_user(str(mentorship.mentor_user_id))
    if student is None or mentor is None:
        return  # No debería pasar, pero no tumbamos la confirmación por un correo.

    date_str = slot.date.isoformat()
    start_str = slot.start_time.strftime("%H:%M")
    end_str = slot.end_time.strftime("%H:%M")

    try:
        send_mentorship_confirmation(student["email"], mentor["nombre"], date_str, start_str, end_str)
        send_mentorship_confirmation(mentor["email"], student["nombre"], date_str, start_str, end_str)
    except Exception:
        pass  # Mismo criterio que en Auth Service: el correo no debe tumbar la operación.


# --- RQF-026: configuración de aceptación de la mentora ---

@router.get("/mentors/me/settings", response_model=MentorSettingsOut)
def get_my_settings(db: Session = Depends(get_db), session: dict = Depends(require_mentor)):
    """Acceso: rol Mentora."""
    mentor_id = uuid.UUID(session["user_id"])
    return _get_or_create_settings(db, mentor_id)


@router.put("/mentors/me/settings", response_model=MentorSettingsOut)
def update_my_settings(
    payload: MentorSettingsUpdate,
    db: Session = Depends(get_db),
    session: dict = Depends(require_mentor),
):
    """Acceso: rol Mentora."""
    mentor_id = uuid.UUID(session["user_id"])
    settings_row = _get_or_create_settings(db, mentor_id)
    settings_row.auto_accept = payload.auto_accept
    db.commit()
    db.refresh(settings_row)
    return settings_row


# --- RQF-028: solicitud de mentoría ---

@router.post("/mentorships", response_model=MentorshipOut, status_code=status.HTTP_201_CREATED)
async def request_mentorship(
    payload: MentorshipRequestCreate,
    db: Session = Depends(get_db),
    session: dict = Depends(get_current_session),
):
    """Acceso: cualquier usuaria autenticada (Mentee, Mentora o Administradora)."""
    if session.get("role_id") != str(MENTEE_ROLE_ID):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo un estudiante puede solicitar mentoría")

    student_id = uuid.UUID(session["user_id"])

    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == payload.availability_slot_id).first()
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bloque de disponibilidad no encontrado")

    # Orden de bloqueo fijo (mentora, luego bloque) para evitar interbloqueos entre solicitudes simultáneas (ASR-26/27).
    settings_row = _lock_settings(db, slot.mentor_user_id)
    slot = (
        db.query(AvailabilitySlot).filter(AvailabilitySlot.id == payload.availability_slot_id)
        .with_for_update().populate_existing().first()
    )
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bloque de disponibilidad no encontrado")
    if slot.status != "libre":
        raise HTTPException(status.HTTP_409_CONFLICT, "Este bloque ya no está disponible")

    confirmed_count = _confirmed_count_in_week(db, slot.mentor_user_id, slot.date)

    if confirmed_count >= settings_row.weekly_limit:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta mentora alcanzó su límite de mentorías esta semana")

    will_auto_confirm = settings_row.auto_accept
    new_status = "confirmada" if will_auto_confirm else "pendiente"

    # Un bloque liberado por una cancelación o un rechazo conserva la fila de la solicitud anterior,
    # y availability_slot_id es único: se descarta para que el bloque pueda volver a reservarse.
    db.query(Mentorship).filter(
        Mentorship.availability_slot_id == slot.id,
        Mentorship.status.in_(["cancelada", "rechazada"]),
    ).delete(synchronize_session=False)

    mentorship = Mentorship(
        student_user_id=student_id,
        mentor_user_id=slot.mentor_user_id,
        availability_slot_id=slot.id,
        status=new_status,
        confirmed_at=datetime.now(timezone.utc) if will_auto_confirm else None,
    )
    db.add(mentorship)

    # El bloque queda "reservado" tanto si confirma como si queda pendiente —
    # evita que dos estudiantes soliciten el mismo horario mientras se decide.
    slot.status = "reservado"

    try:
        db.commit()
    except IntegrityError:
        # Red de seguridad: si aun así otra solicitud tomó el bloque, es un conflicto (409), no un error del servidor.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Este bloque ya no está disponible")
    db.refresh(mentorship)

    if will_auto_confirm:
        await _send_confirmation_emails(db, mentorship, slot)

    return mentorship


# --- RQF-029: respuesta a solicitudes pendientes ---

async def _to_out(db: Session, mentorships: list[Mentorship]) -> list[MentorshipOut]:
    """Completa cada mentoría con el nombre de las dos personas y el horario del bloque,
    para que el frontend no dependa de datos guardados en el navegador."""
    if not mentorships:
        return []

    try:
        names = {u["id"]: u["nombre"] for u in await list_users_internal()}
    except Exception:
        names = {}  # Si Auth no responde, la lista se entrega igual, sin nombres.

    slot_ids = {m.availability_slot_id for m in mentorships}
    slots = {s.id: s for s in db.query(AvailabilitySlot).filter(AvailabilitySlot.id.in_(slot_ids)).all()}

    result = []
    for m in mentorships:
        out = MentorshipOut.model_validate(m)
        out.student_nombre = names.get(str(m.student_user_id))
        out.mentor_nombre = names.get(str(m.mentor_user_id))
        slot = slots.get(m.availability_slot_id)
        if slot is not None:
            out.slot_date = slot.date
            out.slot_start_time = slot.start_time
            out.slot_end_time = slot.end_time
        result.append(out)
    return result


@router.get("/mentors/me/mentorships", response_model=list[MentorshipOut])
async def list_my_mentor_requests(db: Session = Depends(get_db), session: dict = Depends(require_mentor)):
    """Acceso: rol Mentora."""
    mentor_id = uuid.UUID(session["user_id"])
    rows = db.query(Mentorship).filter(Mentorship.mentor_user_id == mentor_id).order_by(Mentorship.created_at.desc()).all()
    return await _to_out(db, rows)


@router.get("/students/me/mentorships", response_model=list[MentorshipOut])
async def list_my_student_requests(db: Session = Depends(get_db), session: dict = Depends(get_current_session)):
    """Acceso: cualquier usuaria autenticada (Mentee, Mentora o Administradora)."""
    student_id = uuid.UUID(session["user_id"])
    rows = db.query(Mentorship).filter(Mentorship.student_user_id == student_id).order_by(Mentorship.created_at.desc()).all()
    return await _to_out(db, rows)


@router.post("/mentorships/{mentorship_id}/accept", response_model=MentorshipOut)
async def accept_mentorship(
    mentorship_id: uuid.UUID,
    db: Session = Depends(get_db),
    session: dict = Depends(require_mentor),
):
    """Acceso: rol Mentora."""
    mentor_id = uuid.UUID(session["user_id"])
    settings_row = _lock_settings(db, mentor_id)  # serializa el conteo del límite semanal (ASR-27)
    mentorship = db.query(Mentorship).filter(
        Mentorship.id == mentorship_id, Mentorship.mentor_user_id == mentor_id
    ).with_for_update().populate_existing().first()
    if mentorship is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitud no encontrada")
    if mentorship.status != "pendiente":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta solicitud ya fue resuelta")

    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == mentorship.availability_slot_id).first()

    if _confirmed_count_in_week(db, mentor_id, slot.date) >= settings_row.weekly_limit:
        raise HTTPException(status.HTTP_409_CONFLICT, "Aceptar esta solicitud superaría tu límite semanal")

    mentorship.status = "confirmada"
    mentorship.confirmed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mentorship)

    await _send_confirmation_emails(db, mentorship, slot)
    return mentorship


@router.post("/mentorships/{mentorship_id}/reject", response_model=MentorshipOut)
def reject_mentorship(
    mentorship_id: uuid.UUID,
    db: Session = Depends(get_db),
    session: dict = Depends(require_mentor),
):
    """Acceso: rol Mentora."""
    mentor_id = uuid.UUID(session["user_id"])
    mentorship = db.query(Mentorship).filter(
        Mentorship.id == mentorship_id, Mentorship.mentor_user_id == mentor_id
    ).first()
    if mentorship is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Solicitud no encontrada")
    if mentorship.status != "pendiente":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta solicitud ya fue resuelta")

    mentorship.status = "rechazada"

    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == mentorship.availability_slot_id).first()
    if slot is not None:
        slot.status = "libre"  # Libera el bloque para que otro estudiante lo tome.

    db.commit()
    db.refresh(mentorship)
    return mentorship


@router.post("/mentorships/{mentorship_id}/cancel", response_model=MentorshipOut)
def cancel_mentorship(
    mentorship_id: uuid.UUID,
    db: Session = Depends(get_db),
    session: dict = Depends(get_current_session),
):
    """Acceso: cualquier usuaria autenticada (Mentee, Mentora o Administradora)."""
    user_id = uuid.UUID(session["user_id"])
    mentorship = db.query(Mentorship).filter(
        Mentorship.id == mentorship_id,
    ).filter(
        (Mentorship.student_user_id == user_id) | (Mentorship.mentor_user_id == user_id)
    ).first()
    if mentorship is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mentoría no encontrada")
    if mentorship.status not in ("pendiente", "confirmada"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esta mentoría no se puede cancelar")

    mentorship.status = "cancelada"

    slot = db.query(AvailabilitySlot).filter(AvailabilitySlot.id == mentorship.availability_slot_id).first()
    if slot is not None:
        slot.status = "libre"

    db.commit()
    db.refresh(mentorship)
    return mentorship


# --- Endpoint interno para Chat Service ---

@router.get("/internal/mentorships/active")
def check_active_mentorship(
    user_a: uuid.UUID,
    user_b: uuid.UUID,
    db: Session = Depends(get_db),
    _key: None = Depends(verify_internal_key),
):
    """Acceso: interno entre servicios (cabecera X-Internal-Key); no es para usuarias finales."""
    exists = db.query(Mentorship).filter(
        Mentorship.status == "confirmada",
        (
            ((Mentorship.student_user_id == user_a) & (Mentorship.mentor_user_id == user_b))
            | ((Mentorship.student_user_id == user_b) & (Mentorship.mentor_user_id == user_a))
        ),
    ).first() is not None
    return {"active": exists}
