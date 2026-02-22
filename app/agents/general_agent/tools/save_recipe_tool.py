"""Save-recipe tool: creates a recipe in the DB and associates it with the current user."""

import logging
from typing import Any

from langchain.tools import tool, ToolRuntime
from pydantic import BaseModel, Field, model_validator

from app.agents.general_agent.schemas import GeneralAgentContext
from app.db_config.session import SessionLocal
from app.services.recipe_service import RecipeService
from app.utils.recipe_utils import normalize_recipe_times

logger = logging.getLogger(__name__)


class SaveRecipeInput(BaseModel):
    """Accept either recipe={{...}} (LLM) or flat recipe fields."""
    recipe: dict[str, Any] | None = Field(None, description="Full recipe object")
    model_config = {"extra": "allow"}

    @model_validator(mode="after")
    def _coerce_recipe(self) -> "SaveRecipeInput":
        if self.recipe:
            return self
        extras = dict(getattr(self, "model_extra") or {})
        extras.pop("runtime", None)  # Exclude injected runtime
        if extras:
            object.__setattr__(self, "recipe", extras)
        return self


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
    out = normalize_recipe_times(out)  # fill times from instruction time_minutes when 0
    return out


@tool(args_schema=SaveRecipeInput)
def save_recipe(runtime: ToolRuntime[GeneralAgentContext], **kwargs: Any) -> str:
    """Save a recipe to the user's collection. Call this when the user asks to save one of the recipes you just showed. Pass the full recipe (name, description, prep_time, cook_time, total_time, servings, difficulty, ingredients, instructions, tags, optional image_url)."""
    inp = SaveRecipeInput.model_validate(kwargs)
    recipe_dict = inp.recipe
    if not recipe_dict:
        return "Cannot save recipe: missing recipe data."
    user_id = getattr(runtime.context, "user_id", None) if runtime else None
    if user_id is None:
        return "Cannot save recipe: user not identified. Please log in."
    payload = _normalize_recipe_payload(recipe_dict)
    # Use sync session to avoid asyncpg "another operation is in progress" when
    # running from LangGraph's sync tool executor (worker thread).
    with SessionLocal() as session:
        try:
            created = RecipeService.create_recipe_sync(session, payload, user_id)
            logger.info("Recipe saved: id=%s name=%s user_id=%s", created.id, created.name, user_id)
            return f'Recipe saved: "{created.name}" (id: {created.id}).'
        except Exception as e:
            logger.exception("Failed to save recipe: %s", e)
            return f"Failed to save recipe: {e!s}"
