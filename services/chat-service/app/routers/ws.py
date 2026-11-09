import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
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
    except HTTPException as exc:
        # 1013 = «intenta de nuevo más tarde» (auth-service caído): el cliente debe reintentar, no darse por vencido.
        await websocket.close(code=1013 if exc.status_code == 503 else 4401)  # 4401: código propio, token inválido
        return
    except Exception:
        await websocket.close(code=4401)
        return

    my_id_str = session["user_id"]
    my_id = uuid.UUID(my_id_str)

    try:
        tiene_mentoria = await has_active_mentorship(my_id_str, str(other_user_id))
    except HTTPException:
        await websocket.close(code=1013)  # navigation-service no responde: reintentar más tarde
        return
    if not tiene_mentoria:
        await websocket.close(code=4403)  # código propio: sin mentoría activa
        return

    db: Session = SessionLocal()
    try:
        conversation_id = get_or_create_conversation(db, my_id, session["role_id"], other_user_id).id
        # Se cierra la transacción abierta por la consulta: con ella pendiente la sesión retendría una conexión del
        # pool mientras la usuaria está conectada sin escribir (DEF-001: ~15 conexiones agotaban el pool y el servicio
        # dejaba de responder). Tras cada commit no se vuelve a leer ningún atributo del modelo, por la misma razón.
        db.rollback()

        await manager.connect(my_id_str, websocket)

        # Avisa a la otra persona, si está conectada, que este usuario acaba de entrar (RQF-019).
        await manager.send_to(str(other_user_id), {"type": "presence", "user_id": my_id_str, "online": True})

        while True:
            data = await websocket.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue  # RQF-016 RN-01: no se procesa un mensaje vacío.

            message = Message(
                conversation_id=conversation_id,
                sender_user_id=my_id,
                content=content,
                status="enviado",
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            message_id, created_at = str(message.id), message.created_at.isoformat()
            db.rollback()  # libera la conexión hasta el próximo mensaje

            delivered = await manager.send_to(str(other_user_id), {
                "type": "message",
                "id": message_id,
                "sender_user_id": my_id_str,
                "content": content,
                "created_at": created_at,
            })

            final_status = "entregado" if delivered else "enviado"
            if delivered:
                db.query(Message).filter(Message.id == message_id).update({"status": final_status})
                db.commit()

            # Confirmación de vuelta al remitente (RQF-016 CA-01, RQF-022 CA-01).
            await websocket.send_json({
                "type": "ack",
                "id": message_id,
                "status": final_status,
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
