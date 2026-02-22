from pydantic import BaseModel, Field
from typing import Optional

from app.schemas.recipe import IngredientItem, InstructionStep


class Recipe(BaseModel):
    """A single recipe with all details (chef agent output shape)."""
    name: str = Field(..., description="The name of the recipe")
    ingredients: list[IngredientItem] = Field(..., description="List of ingredients with name and quantity")
    instructions: list[InstructionStep] = Field(..., description="Step-by-step instructions with step number, description, time and optional chef tip")
    time_to_prepare: int = Field(0, description="Time to prepare in minutes (default 0 if omitted)")
    image_url: Optional[str] = Field(None, description="URL of the recipe image")


class RecipeResponse(BaseModel):
    """Structured response containing exactly one recipe."""
    recipes: list[Recipe] = Field(..., min_length=1, max_length=1, description="List with exactly one recipe")
    source: str = Field("", description="Source of the recipes")
    reasoning: str = Field("", description="Reasoning for the recipe selection")
