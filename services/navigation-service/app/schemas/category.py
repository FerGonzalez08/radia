import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class MentorCategoriesUpdate(BaseModel):
    category_ids: list[uuid.UUID]


class MentorSearchResult(BaseModel):
    mentor_user_id: uuid.UUID
    nombre: str
    email: str
    categories: list[str]
