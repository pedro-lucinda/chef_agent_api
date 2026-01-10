from app.agents.general_agent.prompt import GENERAL_AGENT_PROMPT
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain.agents import AgentState
from langgraph.runtime import Runtime
from langchain.messages import RemoveMessage
from langchain.agents.middleware import before_agent
from typing import Any

@dynamic_prompt
def _user_language_prompt(request: ModelRequest) -> str:
    """Generate system prompt based on user language."""
    user_language = request.runtime.context.user_language
    base_prompt = GENERAL_AGENT_PROMPT

    if user_language != "English":
        return f"{base_prompt} Only respond in {user_language}."
    return base_prompt


@before_agent
def _trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Trim old messages, keeping only the last 10."""
    messages = state["messages"]
    
    # If 10 or fewer messages, no trimming needed
    if len(messages) <= 10:
        return None
    
    # Remove messages BEFORE the last 10 (keep the recent ones)
    messages_to_remove = messages[:-10]
    
    return {"messages": [RemoveMessage(id=m.id) for m in messages_to_remove]}