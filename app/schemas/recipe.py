from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class IngredientItem(BaseModel):
    """Single ingredient with name and quantity."""

    name: str
    quantity: str = Field(..., description="e.g. '2 cups', '200g', '1 tbsp'")


class InstructionStep(BaseModel):
    """Single instruction step with optional chef's tip."""

    step_number: int = Field(..., ge=1, description="1-based step order")
    description: str
    time_minutes: int = Field(..., ge=0, description="Time to complete this step")
    chef_tip: Optional[str] = Field(None, description="Optional chef's tip for this step")

    @model_validator(mode="before")
    @classmethod
    def _normalize_description(cls, data: Any) -> Any:
        """Accept common LLM key variations (desc, descr, step, text) as alias for 'description'."""
        if isinstance(data, dict) and "description" not in data:
            for alt in ("desc", "descr", "step", "text", "instruction"):
                if alt in data and data[alt] is not None:
                    val = data[alt]
                    data = dict(data)
                    data["description"] = val if isinstance(val, str) else str(val)
                    break
        return data


class RecipeCreate(BaseModel):
    """Payload for creating a recipe (REST or save_recipe tool)."""

    name: str
    description: str
    prep_time: int
    cook_time: int
    total_time: int
    servings: int
    difficulty: str
    ingredients: list[IngredientItem]
    instructions: list[InstructionStep]
    tags: list[str] = Field(default_factory=list)
    image_url: Optional[str] = None


class RecipeUpdate(BaseModel):
    """Payload for partial recipe update (PATCH). All fields optional."""

    name: Optional[str] = None
    description: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    total_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    ingredients: Optional[list[IngredientItem]] = None
    instructions: Optional[list[InstructionStep]] = None
    tags: Optional[list[str]] = None
    image_url: Optional[str] = None


class Recipe(BaseModel):
    id: Optional[Union[str, UUID]] = None  # UUID as string in API (accept UUID from ORM)
    name: str
    description: str
    prep_time: int
    cook_time: int
    total_time: int
    servings: int
    difficulty: str
    ingredients: list[IngredientItem]
    instructions: list[InstructionStep]
    tags: list[str]
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
