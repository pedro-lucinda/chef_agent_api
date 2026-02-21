from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


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
