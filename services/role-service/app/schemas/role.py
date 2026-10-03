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


class RoleChangeLogOut(BaseModel):
    """HU-AUDIT - Traza de cambios de rol para el panel de administracion."""

    id: uuid.UUID
    changed_at: datetime

    admin_user_id: uuid.UUID
    admin_nombre: str
    admin_email: str

    target_user_id: uuid.UUID
    target_nombre: str
    target_email: str

    previous_role: str
    new_role: str
