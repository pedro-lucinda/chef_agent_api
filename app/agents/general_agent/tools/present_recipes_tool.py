"""Present-recipes tool: used to trigger HITL so the user can see created recipes and choose to save one or not."""

from typing import Any

from langchain.tools import tool


@tool
def present_recipes_for_save(recipes: list[dict[str, Any]]) -> str:
    """Present the created recipes to the user so they can choose to save one or none.
    Call this immediately after call_chef_agent returns: pass the 'recipes' array from
    the call_chef_agent response (list of recipe objects with name, ingredients, instructions, etc.).
    Do not write out full recipe JSON in chat—use this tool so the user gets a dedicated
    step to view recipes and choose Save recipe 1, 2, 3, or Don't save.
    When the user rejects with 'User chose not to save any recipe', acknowledge and continue.
    When the user rejects with 'User wants to save recipe N', call save_recipe with the
    full payload for that recipe (recipe index N-1 in the recipes list)."""
    # When the tool is actually executed (user approved, e.g. "just continue"), no side effect
    return "Recipes were presented to the user."
