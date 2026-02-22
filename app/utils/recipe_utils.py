"""Shared recipe helpers (e.g. fill prep/cook/total from instruction times)."""


def normalize_recipe_times(recipe: dict) -> dict:
    """
    Return a copy of the recipe with prep_time, cook_time, total_time filled.
    If they are 0 or missing, total_time is set from the sum of instruction time_minutes;
    if prep_time and cook_time are still 0, set cook_time = total_time so the UI shows a non-zero time.
    """
    out = dict(recipe)
    prep = out.get("prep_time", 0) or 0
    cook = out.get("cook_time", 0) or 0
    total = out.get("total_time", 0) or 0

    if total == 0:
        instructions = out.get("instructions") or []
        if isinstance(instructions, list):
            for step in instructions:
                if isinstance(step, dict):
                    total += int(step.get("time_minutes", 0) or 0)
                else:
                    total += int(getattr(step, "time_minutes", 0) or 0)
        out["total_time"] = total

    if prep == 0 and cook == 0 and total > 0:
        out["cook_time"] = total
        out["prep_time"] = 0
    else:
        out.setdefault("prep_time", prep)
        out.setdefault("cook_time", cook)
        out.setdefault("total_time", total)

    return out
