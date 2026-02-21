"""Save-recipe tool: creates a recipe in the DB and associates it with the current user."""

import logging
from typing import Any

from langchain.tools import tool, ToolRuntime

from app.agents.general_agent.schemas import GeneralAgentContext
from app.db_config.db_async_session import async_session
from app.services.recipe_service import RecipeService

logger = logging.getLogger(__name__)


def _normalize_recipe_payload(data: dict) -> dict:
    """Normalize chef shape (time_to_prepare) to DB shape (prep_time, cook_time, total_time)."""
    out = dict(data)
    if "time_to_prepare" in out and "total_time" not in out:
        out["total_time"] = out["time_to_prepare"]
        out.setdefault("prep_time", 0)
        out.setdefault("cook_time", 0)
        del out["time_to_prepare"]
    out.setdefault("description", out.get("name", "") or "")
    out.setdefault("prep_time", 0)
    out.setdefault("cook_time", 0)
    out.setdefault("total_time", out.get("prep_time", 0) + out.get("cook_time", 0))
    out.setdefault("servings", 1)
    out.setdefault("difficulty", "medium")
    out.setdefault("tags", [])
    out.setdefault("image_url", None)
    return out


@tool
async def save_recipe(recipe: dict[str, Any], runtime: ToolRuntime[GeneralAgentContext]) -> str:
    """Save a recipe to the user's collection. Call this when the user asks to save one of the recipes you just showed. Pass the full recipe (name, description, prep_time, cook_time, total_time, servings, difficulty, ingredients, instructions, tags, optional image_url)."""
    user_id = getattr(runtime.context, "user_id", None) if runtime.context else None
    if user_id is None:
        return "Cannot save recipe: user not identified. Please log in."
    payload = _normalize_recipe_payload(recipe)
    async with async_session() as session:
        service = RecipeService(session)
        try:
            created = await service.create_recipe(payload, user_id)
            logger.info("Recipe saved: id=%s name=%s user_id=%s", created.id, created.name, user_id)
            return f"Recipe saved: “{created.name}” (id: {created.id})."
        except Exception as e:
            logger.exception("Failed to save recipe: %s", e)
            return f"Failed to save recipe: {e!s}"
