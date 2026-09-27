import uuid
from datetime import datetime

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_user_id: uuid.UUID
    content: str
    status: str
    created_at: datetime
    read_at: datetime | None

    class Config:
        from_attributes = True


class ConversationStatusOut(BaseModel):
    conversation_id: uuid.UUID
    online: bool
    last_seen_at: datetime | None
    unread_count: int
