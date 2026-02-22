import json
from dotenv import load_dotenv
from langchain.agents import create_agent
from app.agents.general_agent.prompt import GENERAL_AGENT_PROMPT
from app.agents.general_agent.tools.chef_agent import call_chef_agent
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
from typing import List, Generator

load_dotenv()


model = ChatOpenAI(model="gpt-5-nano", temperature=0.3)

general_agent = create_agent(
    tools=[call_chef_agent, save_recipe],
    model=model,
    system_prompt=GENERAL_AGENT_PROMPT,
    checkpointer=checkpointer,
    context_schema=GeneralAgentContext,
    middleware=[
        _drop_orphan_tool_calls,
        _user_language_prompt,
        _trim_messages,
        _drop_orphan_tool_messages,
    ],
)

def stream_general_agent(
    messages: List[AnyMessage],
    config: dict,
    context: GeneralAgentContext,
) -> Generator[str, None, None]:
    """Stream the general agent response with structured JSON events."""
    stream = general_agent.stream(
        {"messages": messages},
        stream_mode=["updates", "messages"],
        config=config,
        context=context,
    )
    for mode, chunk in stream:
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

