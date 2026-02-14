import json
from dotenv import load_dotenv
from langchain.agents import create_agent
from app.agents.general_agent.tools.web_search_tool import web_search, web_search_image
from app.agents.general_agent.prompt import GENERAL_AGENT_PROMPT
from app.agents.general_agent.tools.chef_agent import call_chef_agent
from app.agents.general_agent.middlewares import _user_language_prompt, _trim_messages
from app.agents.general_agent.checkpointer import checkpointer
from langchain_core.messages import AnyMessage, AIMessage, ToolMessage
from app.agents.general_agent.schemas import GeneralAgentContext
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Generator

load_dotenv()

model = ChatOpenAI(model="gpt-5-nano", temperature=0.3 )

general_agent = create_agent(
    tools=[call_chef_agent],
    model=model,
    system_prompt=GENERAL_AGENT_PROMPT,
    checkpointer=checkpointer,
    context_schema=GeneralAgentContext,
    middleware=[_user_language_prompt, _trim_messages],
)

  
def stream_general_agent(messages: List[AnyMessage], config: dict, context: GeneralAgentContext) -> Generator[str, None, None]:
    """Stream the general agent response with structured JSON events"""
    
    for token, metadata in general_agent.stream(
        {"messages": messages},
        stream_mode="messages",
        config=config,
        context=context
    ):
        # Stream tool calls
        if isinstance(token, AIMessage) and hasattr(token, 'tool_calls') and token.tool_calls:
            for tool_call in token.tool_calls:
                # Handle both dict and object-style tool calls
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get('name', 'unknown')
                    tool_id = tool_call.get('id', 'unknown')
                    tool_args = tool_call.get('args', {})
                else:
                    tool_name = getattr(tool_call, 'name', 'unknown')
                    tool_id = getattr(tool_call, 'id', 'unknown')
                    tool_args = getattr(tool_call, 'args', {})
                
                yield "data: " + json.dumps({
                    "type": "tool_call",
                    "tool_call": {
                        "id": tool_id,
                        "name": tool_name,
                        "arguments": tool_args
                    }
                }) + "\n\n"
        
        # Stream tool responses
        if isinstance(token, ToolMessage):
            tool_call_id = getattr(token, 'tool_call_id', 'unknown')
            tool_name = getattr(token, 'name', 'unknown')
            content = getattr(token, 'content', '')
            
            yield "data: " + json.dumps({
                "type": "tool_result",
                "tool_result": {
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": str(content) if content else ""
                }
            }) + "\n\n"
        
        # Stream content tokens
        if hasattr(token, 'content') and token.content and not (isinstance(token, AIMessage) and token.tool_calls):
            yield "data: " + json.dumps({
                "type": "data",
                "data": token.content,
                "thread_id": config["configurable"]["thread_id"]
            }) + "\n\n"

