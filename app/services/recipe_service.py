from typing import List, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe as RecipeModel
from app.schemas.recipe import Recipe, RecipeCreate


def _serialize_ingredients(ingredients: list) -> list:
    """Convert ingredients to JSON-serializable list of dicts."""
    if not ingredients:
        return []
    if isinstance(ingredients[0], dict):
        return ingredients
    return [item.model_dump() if hasattr(item, "model_dump") else item for item in ingredients]


def _serialize_instructions(instructions: list) -> list:
    """Convert instructions to JSON-serializable list of dicts."""
    if not instructions:
        return []
    if isinstance(instructions[0], dict):
        return instructions
    return [item.model_dump() if hasattr(item, "model_dump") else item for item in instructions]


class RecipeService:
    """Service layer for recipe operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_recipe(self, recipe_data: Union[dict, RecipeCreate], user_id: int) -> RecipeModel:
        """Create a new recipe and associate with user."""
        if isinstance(recipe_data, RecipeCreate):
            data = recipe_data.model_dump()
        else:
            data = dict(recipe_data)
        ingredients = _serialize_ingredients(data.get("ingredients", []))
        instructions = _serialize_instructions(data.get("instructions", []))
        tags = data.get("tags") or []
        recipe_model = RecipeModel(
            name=data["name"],
            description=data["description"],
            prep_time=data["prep_time"],
            cook_time=data["cook_time"],
            total_time=data["total_time"],
            servings=data["servings"],
            difficulty=data["difficulty"],
            ingredients=ingredients,
            instructions=instructions,
            tags=tags,
            image_url=data.get("image_url"),
            user_id=user_id,
        )
        self.db.add(recipe_model)
        await self.db.commit()
        await self.db.refresh(recipe_model)
        return recipe_model

    async def get_recipe_by_id(self, recipe_id: UUID, user_id: int) -> RecipeModel:
        """Get a recipe by ID (must belong to user)."""
        stmt = select(RecipeModel).where(
            RecipeModel.id == recipe_id,
            RecipeModel.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        recipe = result.scalar_one_or_none()
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )
        return recipe

    async def get_recipes(self, user_id: int) -> List[RecipeModel]:
        """Get all recipes for a user."""
        stmt = select(RecipeModel).where(RecipeModel.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_recipe(self, recipe_id: UUID, user_id: int) -> bool:
        """Delete a recipe by ID (must belong to user)."""
        stmt = select(RecipeModel).where(
            RecipeModel.id == recipe_id,
            RecipeModel.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        recipe = result.scalar_one_or_none()
        if not recipe:
            return False
        await self.db.delete(recipe)
        await self.db.commit()
        return True
