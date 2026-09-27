import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.clients import has_active_mentorship, validate_session
from app.core.connection_manager import manager
from app.core.database import SessionLocal
from app.models.last_seen import LastSeen
from app.models.message import Message
from app.routers.chat import get_or_create_conversation

router = APIRouter()


@router.websocket("/ws/{other_user_id}")
async def chat_websocket(websocket: WebSocket, other_user_id: uuid.UUID, token: str = Query(...)):
    try:
        session = await validate_session(token)
    except Exception:
        await websocket.close(code=4401)  # código propio: token inválido
        return

    my_id_str = session["user_id"]
    my_id = uuid.UUID(my_id_str)

    if not await has_active_mentorship(my_id_str, str(other_user_id)):
        await websocket.close(code=4403)  # código propio: sin mentoría activa
        return

    db: Session = SessionLocal()
    try:
        conversation = get_or_create_conversation(db, my_id, session["role_id"], other_user_id)

        await manager.connect(my_id_str, websocket)

        # Avisa a la otra persona, si está conectada, que este usuario acaba de entrar (RQF-019).
        await manager.send_to(str(other_user_id), {"type": "presence", "user_id": my_id_str, "online": True})

        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue  # RQF-016 RN-01: no se procesa un mensaje vacío.

            message = Message(
                conversation_id=conversation.id,
                sender_user_id=my_id,
                content=content,
                status="enviado",
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            delivered = await manager.send_to(str(other_user_id), {
                "type": "message",
                "id": str(message.id),
                "sender_user_id": my_id_str,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            })

            message.status = "entregado" if delivered else "enviado"
            db.commit()

            # Confirmación de vuelta al remitente (RQF-016 CA-01, RQF-022 CA-01).
            await websocket.send_json({
                "type": "ack",
                "id": str(message.id),
                "status": message.status,
            })

    except WebSocketDisconnect:
        pass
    finally:
        was_last_session = manager.disconnect(my_id_str, websocket)

        if was_last_session:
            existing = db.query(LastSeen).filter(LastSeen.user_id == my_id).first()
            now = datetime.now(timezone.utc)
            if existing is None:
                db.add(LastSeen(user_id=my_id, last_seen_at=now))
            else:
                existing.last_seen_at = now
            db.commit()

            await manager.send_to(str(other_user_id), {
                "type": "presence", "user_id": my_id_str, "online": False, "last_seen_at": now.isoformat(),
            })

        db.close()
