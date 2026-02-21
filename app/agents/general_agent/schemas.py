from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.recipe import Recipe


class GeneralAgentContext(BaseModel):
    user_language: str = Field(default="English")
    user_id: Optional[int] = Field(default=None, description="Current user ID for save_recipe tool")
    recipe: Optional[Recipe] = Field(default=None)