import uuid
from datetime import date, datetime, time

from pydantic import BaseModel


class MentorshipRequestCreate(BaseModel):
    availability_slot_id: uuid.UUID


class MentorshipOut(BaseModel):
    id: uuid.UUID
    student_user_id: uuid.UUID
    mentor_user_id: uuid.UUID
    availability_slot_id: uuid.UUID
    status: str
    created_at: datetime
    confirmed_at: datetime | None
    student_nombre: str | None = None
    mentor_nombre: str | None = None
    slot_date: date | None = None
    slot_start_time: time | None = None
    slot_end_time: time | None = None

    class Config:
        from_attributes = True


class MentorSettingsOut(BaseModel):
    mentor_user_id: uuid.UUID
    auto_accept: bool
    weekly_limit: int

    class Config:
        from_attributes = True


class MentorSettingsUpdate(BaseModel):
    auto_accept: bool
