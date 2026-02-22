from pydantic import BaseModel, model_validator
from typing import Any, Literal
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
    recipes: list[dict[str, Any]] | None = None  # from recipe_data for UI to render cards on refresh
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def map_recipe_data_from_orm(cls, v: Any) -> Any:
        """Map ORM recipe_data to recipes when validating from a Message instance."""
        if hasattr(v, "recipe_data"):
            return {
                "id": v.id,
                "content": v.content,
                "role": v.role,
                "thread_id": v.thread_id,
                "created_at": v.created_at,
                "updated_at": v.updated_at,
                "recipes": v.recipe_data,
            }
        return v
