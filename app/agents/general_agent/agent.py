import json
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from app.agents.general_agent.prompt import GENERAL_AGENT_PROMPT
from app.agents.general_agent.tools.chef_agent import call_chef_agent
from app.agents.general_agent.tools.present_recipes_tool import present_recipes_for_save
from app.agents.general_agent.tools.save_recipe_tool import save_recipe
from app.agents.general_agent.middlewares import (
    _drop_orphan_tool_calls,
    _drop_orphan_tool_messages,
    _trim_messages,
    _user_language_prompt,
)
from app.agents.general_agent.checkpointer import checkpointer
from langchain_core.messages import AnyMessage, AIMessage, ToolMessage
from app.agents.general_agent.schemas import GeneralAgentContext
from langchain_openai import ChatOpenAI
from typing import Any, List, Generator

load_dotenv()


def _to_serializable(obj: Any) -> Any:
    """Recursively convert to JSON-serializable form; handle LangGraph Interrupt and nested structures."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(x) for x in obj]
    if type(obj).__name__ == "Interrupt":
        return {
            "value": _to_serializable(getattr(obj, "value", None)),
            "id": getattr(obj, "id", None),
        }
    return str(obj)


model = ChatOpenAI(model="gpt-5-nano", temperature=0.3)

general_agent = create_agent(
    tools=[call_chef_agent, present_recipes_for_save, save_recipe],
    model=model,
    system_prompt=GENERAL_AGENT_PROMPT,
    checkpointer=checkpointer,
    context_schema=GeneralAgentContext,
    middleware=[
        _drop_orphan_tool_calls,
        _user_language_prompt,
        _trim_messages,
        _drop_orphan_tool_messages,
        HumanInTheLoopMiddleware(
            interrupt_on={
                "present_recipes_for_save": True,
                "save_recipe": True,
            },
            description_prefix="Save recipe to your collection?",
        ),
    ],
)

def stream_general_agent(
    messages: List[AnyMessage],
    config: dict,
    context: GeneralAgentContext,
) -> Generator[str, None, None]:
    """Stream the general agent response with structured JSON events. Emits interrupt event when HITL pauses."""
    stream = general_agent.stream(
        {"messages": messages},
        stream_mode=["updates", "messages"],
        config=config,
        context=context,
    )
    for mode, chunk in stream:
        # HITL: emit interrupt and stop so client can show approve/reject
        if mode == "updates" and isinstance(chunk, dict) and "__interrupt__" in chunk:
            interrupt_value = chunk["__interrupt__"]
            # Normalize to list of interrupt items (LangGraph may wrap in list)
            if not isinstance(interrupt_value, list):
                interrupt_value = [interrupt_value]
            payload = _to_serializable(interrupt_value)
            yield "data: " + json.dumps({
                "type": "interrupt",
                "interrupt": payload,
                "thread_id": config["configurable"].get("thread_id"),
            }) + "\n\n"
            return
        if mode != "messages":
            continue
        token, metadata = chunk
        # Stream tool calls (skip empty/placeholder entries from the runtime)
        if isinstance(token, AIMessage) and getattr(token, "tool_calls", None):
            for tool_call in token.tool_calls:
                if isinstance(tool_call, dict):
                    tool_id = tool_call.get("id")
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("args", {})
                else:
                    tool_id = getattr(tool_call, "id", None)
                    tool_name = getattr(tool_call, "name", None)
                    tool_args = getattr(tool_call, "args", {})
                if not tool_id or not tool_name:
                    continue
                yield "data: " + json.dumps({
                    "type": "tool_call",
                    "tool_call": {"id": tool_id, "name": tool_name, "arguments": tool_args or {}},
                }) + "\n\n"
        # Stream tool responses
        if isinstance(token, ToolMessage):
            tool_call_id = getattr(token, "tool_call_id", "unknown")
            tool_name = getattr(token, "name", "unknown")
            content = getattr(token, "content", "")
            yield "data: " + json.dumps({
                "type": "tool_result",
                "tool_result": {
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": str(content) if content else "",
                },
            }) + "\n\n"
        # Stream content tokens
        if hasattr(token, "content") and token.content and not (
            isinstance(token, AIMessage) and getattr(token, "tool_calls", None)
        ):
            yield "data: " + json.dumps({
                "type": "data",
                "data": token.content,
                "thread_id": config["configurable"].get("thread_id"),
            }) + "\n\n"


def stream_general_agent_resume(
    config: dict,
    context: GeneralAgentContext,
    decisions: list[dict],
) -> Generator[str, None, None]:
    """Stream the rest of the agent response after HITL resume (approve/reject)."""
    from langgraph.types import Command
    stream = general_agent.stream(
        Command(resume={"decisions": decisions}),
        stream_mode=["updates", "messages"],
        config=config,
        context=context,
    )
    for mode, chunk in stream:
        if mode == "updates" and isinstance(chunk, dict) and "__interrupt__" in chunk:
            interrupt_value = chunk["__interrupt__"]
            if not isinstance(interrupt_value, list):
                interrupt_value = [interrupt_value]
            payload = _to_serializable(interrupt_value)
            yield "data: " + json.dumps({
                "type": "interrupt",
                "interrupt": payload,
                "thread_id": config["configurable"].get("thread_id"),
            }) + "\n\n"
            return
        if mode != "messages":
            continue
        token, metadata = chunk
        if isinstance(token, AIMessage) and getattr(token, "tool_calls", None):
            for tool_call in token.tool_calls:
                tc = tool_call if isinstance(tool_call, dict) else {}
                tid, tname = tc.get("id"), tc.get("name")
                if not tid or not tname:
                    continue
                yield "data: " + json.dumps({
                    "type": "tool_call",
                    "tool_call": {
                        "id": tid,
                        "name": tname,
                        "arguments": tc.get("args") or {},
                    },
                }) + "\n\n"
        if isinstance(token, ToolMessage):
            yield "data: " + json.dumps({
                "type": "tool_result",
                "tool_result": {
                    "tool_call_id": getattr(token, "tool_call_id", "unknown"),
                    "name": getattr(token, "name", "unknown"),
                    "content": str(getattr(token, "content", "") or ""),
                },
            }) + "\n\n"
        if hasattr(token, "content") and token.content and not (
            isinstance(token, AIMessage) and getattr(token, "tool_calls", None)
        ):
            yield "data: " + json.dumps({
                "type": "data",
                "data": token.content,
                "thread_id": config["configurable"].get("thread_id"),
            }) + "\n\n"

