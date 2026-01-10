from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from uuid import UUID


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    thread_id: UUID
    content: str
    role: Literal["user", "assistant"]

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    """Schema for message output."""
    id: UUID
    content: str
    role: Literal["user", "assistant"]
    thread_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
