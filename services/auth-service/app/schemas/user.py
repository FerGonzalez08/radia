import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=1, max_length=150)
    telefono: str = Field(min_length=1, max_length=20)
    sexo: str = Field(min_length=1, max_length=20)
    fecha_nacimiento: date
    


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    nombre: str
    telefono: str
    sexo: str
    fecha_nacimiento: date
    role_id: uuid.UUID
    is_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RoleUpdateRequest(BaseModel):
    role_id: uuid.UUID


class RoleUpdateRequest(BaseModel):
    role_id: uuid.UUID
