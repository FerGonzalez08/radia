import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_session, require_mentor
from app.models.availability_slot import AvailabilitySlot
from app.models.mentorship import Mentorship
from app.schemas.availability import AvailabilitySlotCreate, AvailabilitySlotOut

router = APIRouter(tags=["availability"])

def _naive(t):
    return t.replace(tzinfo=None) if t.tzinfo else t

def _overlaps(db: Session, mentor_id: uuid.UUID, payload: AvailabilitySlotCreate) -> bool:
    existing_slots = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.mentor_user_id == mentor_id,
        AvailabilitySlot.date == payload.date,
    ).all()

    new_start = _naive(payload.start_time)
    new_end = _naive(payload.end_time)

    for slot in existing_slots:
        if new_start < slot.end_time and new_end > slot.start_time:
            return True
    return False


@router.get("/mentors/me/availability", response_model=list[AvailabilitySlotOut])
def list_my_availability(
    db: Session = Depends(get_db),
    session: dict = Depends(require_mentor),
):
    mentor_id = uuid.UUID(session["user_id"])
    return (
        db.query(AvailabilitySlot)
        .filter(AvailabilitySlot.mentor_user_id == mentor_id)
        .order_by(AvailabilitySlot.date, AvailabilitySlot.start_time)
        .all()
    )


@router.post("/mentors/me/availability", response_model=AvailabilitySlotOut, status_code=status.HTTP_201_CREATED)
def create_availability_slot(
    payload: AvailabilitySlotCreate,
    db: Session = Depends(get_db),
    session: dict = Depends(require_mentor),
):
    mentor_id = uuid.UUID(session["user_id"])

    if payload.end_time <= payload.start_time:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La hora de fin debe ser posterior a la de inicio")

    if _overlaps(db, mentor_id, payload):
        raise HTTPException(status.HTTP_409_CONFLICT, "Este horario se traslapa con uno existente")

    slot = AvailabilitySlot(
        mentor_user_id=mentor_id,
        date=payload.date,
        start_time=_naive(payload.start_time),
        end_time=_naive(payload.end_time),
        status="libre",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.delete("/mentors/me/availability/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability_slot(
    slot_id: uuid.UUID,
    db: Session = Depends(get_db),
    session: dict = Depends(require_mentor),
):
    mentor_id = uuid.UUID(session["user_id"])
    slot = db.query(AvailabilitySlot).filter(
        AvailabilitySlot.id == slot_id,
        AvailabilitySlot.mentor_user_id == mentor_id,
    ).first()

    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bloque no encontrado")

    linked_mentorship = db.query(Mentorship).filter(
        Mentorship.availability_slot_id == slot_id,
        Mentorship.status.in_(["pendiente", "confirmada"]),
    ).first()
    if linked_mentorship is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "No puedes eliminar un bloque con una mentoría activa")

    # Las solicitudes canceladas o rechazadas de este bloque son solo historial de intentos fallidos;
    # se descartan para que la clave foránea no impida borrar el bloque.
    db.query(Mentorship).filter(
        Mentorship.availability_slot_id == slot_id,
        Mentorship.status.in_(["cancelada", "rechazada"]),
    ).delete(synchronize_session=False)

    db.delete(slot)
    db.commit()
    return None


@router.get("/mentors/{mentor_id}/availability", response_model=list[AvailabilitySlotOut])
def list_mentor_public_availability(
    mentor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _session: dict = Depends(get_current_session),
):
    # Vista pública (para el estudiante) — solo bloques libres, no todos.
    return (
        db.query(AvailabilitySlot)
        .filter(AvailabilitySlot.mentor_user_id == mentor_id, AvailabilitySlot.status == "libre")
        .order_by(AvailabilitySlot.date, AvailabilitySlot.start_time)
        .all()
    )
