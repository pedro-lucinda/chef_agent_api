from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.api.v1.dependencies.auth0 import get_current_user
from app.api.v1.dependencies.async_db_session import get_async_db
from app.schemas.recipe import Recipe, RecipeCreate
from app.services.recipe_service import RecipeService
from app.models.user import User as UserModel

router = APIRouter()


@router.post("/", response_model=Recipe, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe: RecipeCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> Recipe:
    """Create a new recipe."""
    return await RecipeService(db).create_recipe(recipe.model_dump(), current_user.id)

@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe_by_id(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> Recipe:
    """Get a recipe by ID."""
    return await RecipeService(db).get_recipe_by_id(recipe_id, current_user.id)

@router.get("/", response_model=List[Recipe])
async def get_recipes(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> List[Recipe]:
    """Get all recipes."""
    return await RecipeService(db).get_recipes(current_user.id)

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> None:
    """Delete a recipe by ID."""
    await RecipeService(db).delete_recipe(recipe_id, current_user.id)
