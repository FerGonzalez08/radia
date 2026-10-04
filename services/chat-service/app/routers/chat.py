import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.clients import has_active_mentorship, validate_session
from app.core.config import MENTOR_ROLE_ID
from app.core.connection_manager import manager
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.last_seen import LastSeen
from app.models.message import Message
from app.schemas.chat import ConversationStatusOut, MessageOut
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(tags=["chat"])
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_session(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return await validate_session(credentials.credentials)


def get_or_create_conversation(db: Session, my_id: uuid.UUID, my_role: str, other_id: uuid.UUID) -> Conversation:
    if my_role == str(MENTOR_ROLE_ID):
        student_id, mentor_id = other_id, my_id
    else:
        student_id, mentor_id = my_id, other_id

    conversation = db.query(Conversation).filter(
        Conversation.student_user_id == student_id,
        Conversation.mentor_user_id == mentor_id,
    ).first()

    if conversation is None:
        conversation = Conversation(student_user_id=student_id, mentor_user_id=mentor_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation


@router.get("/conversations/{other_user_id}/messages", response_model=list[MessageOut])
async def get_history(
    other_user_id: uuid.UUID,
    before: datetime | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
    session: dict = Depends(get_current_session),
):
    my_id = uuid.UUID(session["user_id"])

    if not await has_active_mentorship(str(my_id), str(other_user_id)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No hay una mentoría activa entre estos usuarios")

    conversation = get_or_create_conversation(db, my_id, session["role_id"], other_user_id)

    query = db.query(Message).filter(Message.conversation_id == conversation.id)
    if before is not None:
        query = query.filter(Message.created_at < before)

    # Traemos en orden descendente para paginar "hacia atrás", y revertimos antes de devolver
    # para que el cliente reciba los mensajes en orden cronológico normal.
    messages = query.order_by(Message.created_at.desc()).limit(limit).all()
    return list(reversed(messages))


@router.post("/conversations/{other_user_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    other_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    session: dict = Depends(get_current_session),
):
    my_id = uuid.UUID(session["user_id"])

    if not await has_active_mentorship(str(my_id), str(other_user_id)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No hay una mentoría activa entre estos usuarios")

    conversation = get_or_create_conversation(db, my_id, session["role_id"], other_user_id)

    db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_user_id == other_user_id,
        Message.read_at.is_(None),
    ).update({"read_at": datetime.now(timezone.utc)})
    db.commit()
    return None


@router.get("/conversations/{other_user_id}/status", response_model=ConversationStatusOut)
async def get_status(
    other_user_id: uuid.UUID,
    db: Session = Depends(get_db),
    session: dict = Depends(get_current_session),
):
    my_id = uuid.UUID(session["user_id"])

    if not await has_active_mentorship(str(my_id), str(other_user_id)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No hay una mentoría activa entre estos usuarios")

    conversation = get_or_create_conversation(db, my_id, session["role_id"], other_user_id)

    unread_count = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_user_id == other_user_id,
        Message.read_at.is_(None),
    ).count()

    last_seen = db.query(LastSeen).filter(LastSeen.user_id == other_user_id).first()

    return ConversationStatusOut(
        conversation_id=conversation.id,
        online=manager.is_online(str(other_user_id)),
        last_seen_at=last_seen.last_seen_at if last_seen else None,
        unread_count=unread_count,
    )
