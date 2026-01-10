from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.schemas.message import MessageOut


class ThreadCreate(BaseModel):
    """Schema for creating a thread (user_id comes from auth)."""
    pass  # No fields needed - user_id comes from authenticated user


class ThreadOut(BaseModel):
    """Schema for thread output."""
    id: UUID
    user_id: int  # User.id is still Integer
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageOut]] = None

    class Config:
        from_attributes = True
