from datetime import datetime, timedelta
from typing import List, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.recipe import Recipe as RecipeModel
from app.schemas.recipe import Recipe, RecipeCreate, RecipeUpdate


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

    @staticmethod
    def create_recipe_sync(db: Session, recipe_data: Union[dict, RecipeCreate], user_id: int) -> RecipeModel:
        """Create a recipe synchronously. Use when running from sync context (e.g. LangGraph tool)."""
        if isinstance(recipe_data, RecipeCreate):
            data = recipe_data.model_dump()
        else:
            data = dict(recipe_data)
        name = data.get("name") or ""
        # Idempotency: if same name+user was created in the last 2 minutes (e.g. resume + tool both saving), return it
        since = datetime.utcnow() - timedelta(minutes=2)
        existing = (
            db.query(RecipeModel)
            .where(
                RecipeModel.user_id == user_id,
                RecipeModel.name == name,
                RecipeModel.created_at >= since,
            )
            .order_by(RecipeModel.created_at.desc())
            .first()
        )
        if existing:
            return existing
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
        db.add(recipe_model)
        db.commit()
        db.refresh(recipe_model)
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

    async def update_recipe(
        self, recipe_id: UUID, recipe_data: Union[dict, RecipeUpdate], user_id: int
    ) -> RecipeModel:
        """Update a recipe by ID (must belong to user)."""
        recipe = await self.get_recipe_by_id(recipe_id, user_id)
        if isinstance(recipe_data, RecipeUpdate):
            data = recipe_data.model_dump(exclude_unset=True)
        else:
            data = {k: v for k, v in recipe_data.items() if v is not None}
        if "ingredients" in data and data["ingredients"] is not None:
            data["ingredients"] = _serialize_ingredients(data["ingredients"])
        if "instructions" in data and data["instructions"] is not None:
            data["instructions"] = _serialize_instructions(data["instructions"])
        for key, value in data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)
        await self.db.commit()
        await self.db.refresh(recipe)
        return recipe

    async def delete_recipe(self, recipe_id: UUID, user_id: int) -> None:
        """Delete a recipe by ID (must belong to user). Raises 404 if not found."""
        recipe = await self.get_recipe_by_id(recipe_id, user_id)
        await self.db.delete(recipe)
        await self.db.commit()
