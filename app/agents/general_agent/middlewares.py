from typing import Any

from langchain.agents import AgentState
from langchain.agents.middleware import before_agent, dynamic_prompt, ModelRequest
from langchain.messages import RemoveMessage
from langgraph.runtime import Runtime

from langchain_core.messages import AIMessage, ToolMessage

from app.agents.general_agent.prompt import GENERAL_AGENT_PROMPT


def _get_tool_call_ids(msg: AIMessage) -> set[str]:
    """Extract tool_call ids from an AIMessage."""
    ids = set()
    for tc in getattr(msg, "tool_calls", []) or []:
        tid = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
        if tid:
            ids.add(tid)
    return ids


def _preceding_ai_has_tool_call(messages: list, i: int) -> bool:
    """True if messages[i] is a ToolMessage and the preceding message is an AIMessage with a matching tool_call."""
    if i <= 0 or i >= len(messages):
        return False
    msg = messages[i]
    if not isinstance(msg, ToolMessage):
        return False
    prev = messages[i - 1]
    if not isinstance(prev, AIMessage):
        return False
    tool_call_id = getattr(msg, "tool_call_id", None)
    if not tool_call_id:
        return False
    return tool_call_id in _get_tool_call_ids(prev)


@before_agent
def _drop_orphan_tool_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Remove ToolMessages that do not follow an AIMessage with a matching tool_call.
    Prevents OpenAI 400: messages with role 'tool' must be a response to a preceding message with 'tool_calls'.
    Can occur after trimming when the preceding AIMessage was removed."""
    messages = state.get("messages") or []
    to_remove = [
        m for i, m in enumerate(messages)
        if isinstance(m, ToolMessage) and not _preceding_ai_has_tool_call(messages, i)
    ]
    if not to_remove:
        return None
    return {"messages": [RemoveMessage(id=m.id) for m in to_remove]}


@before_agent
def _drop_orphan_tool_calls(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Remove the last AIMessage if it has tool_calls with no following ToolMessages.
    Prevents OpenAI 400: 'An assistant message with tool_calls must be followed by tool messages'."""
    messages = state.get("messages") or []
    if not messages:
        return None
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if not isinstance(msg, AIMessage):
            continue
        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            continue
        pending = _get_tool_call_ids(msg)
        for j in range(i + 1, len(messages)):
            if isinstance(messages[j], ToolMessage):
                tid = getattr(messages[j], "tool_call_id", None)
                if tid:
                    pending.discard(tid)
        if pending:
            return {"messages": [RemoveMessage(id=msg.id)]}
        break
    return None


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