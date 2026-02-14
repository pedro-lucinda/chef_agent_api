from pydantic import BaseModel, Field
from typing import Optional


class Recipe(BaseModel):
    """A single recipe with all details."""
    name: str = Field(..., description="The name of the recipe")
    ingredients: list[str] = Field(..., description="List of ingredients needed")
    instructions: list[str] = Field(..., description="Step-by-step cooking instructions")
    time_to_prepare: int = Field(..., description="Time to prepare in minutes")
    image_url: Optional[str] = Field(None, description="URL of the recipe image")


class RecipeResponse(BaseModel):
    """Structured response containing recipes."""
    recipes: list[Recipe] = Field(..., description="List of recipes")
    source: str = Field(..., description="Source of the recipes")
    reasoning: str = Field(..., description="Reasoning for the recipe selection")
