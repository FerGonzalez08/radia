import uuid
from datetime import datetime

from pydantic import BaseModel


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithRoleOut(BaseModel):
    id: str
    email: str
    nombre: str
    role_id: str
    is_verified: bool
    is_active: bool
