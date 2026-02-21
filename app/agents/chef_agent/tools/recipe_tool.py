from langchain.tools import tool, ToolRuntime
from app.schemas.recipe import Recipe
from app.models.recipe import Recipe as RecipeModel
from app.db_config.session import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

@tool
async def create_recipe(runtime: ToolRuntime) -> AsyncSession:
    """Create a new recipe"""
    recipe = runtime.state["recipe"]
    async with SessionLocal() as session:
        recipe_model = RecipeModel(
            name=recipe.name,
            description=recipe.description,
            ingredients=recipe.ingredients,
            instructions=recipe.instructions,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            total_time=recipe.total_time,
            servings=recipe.servings,
            difficulty=recipe.difficulty,
            tags=recipe.tags,
        )
        session.add(recipe_model)
        await session.commit()
        return recipe_model