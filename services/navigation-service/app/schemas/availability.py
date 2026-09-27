import uuid
from datetime import date, time

from pydantic import BaseModel


class AvailabilitySlotCreate(BaseModel):
    date: date
    start_time: time
    end_time: time


class AvailabilitySlotOut(BaseModel):
    id: uuid.UUID
    mentor_user_id: uuid.UUID
    date: date
    start_time: time
    end_time: time
    status: str

    class Config:
        from_attributes = True
