from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command


@tool
def update_language_state(
    runtime: ToolRuntime
) -> Command:
    """Update the language state of the user in the state once they've revealed it."""
    tool_call_id = runtime.state["tool_call_id"]
    user_language = runtime.state["user_language"]
    return Command(update={
        "user_language": user_language, 
        "messages": [ToolMessage("Successfully updated language", tool_call_id=tool_call_id)]
    })

@tool
def update_recipe_state(
    runtime: ToolRuntime
) -> Command:
    """Update the recipe state of the user in the state once they've revealed it."""
    tool_call_id = runtime.state["tool_call_id"]
    recipe = runtime.state["recipe"]
    return Command(update={
        "recipe": recipe,
        "messages": [ToolMessage("Successfully updated recipe", tool_call_id=tool_call_id)]
    })