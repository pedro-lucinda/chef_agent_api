import json
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from app.agents.chef_agent.tools.web_search_tool import web_search
from app.agents.chef_agent.prompt import CHEF_AGENT_PROMPT
from app.agents.chef_agent.schemas import RecipeResponse
from langchain_core.messages import AnyMessage, AIMessage, ToolMessage
from typing import List, Generator

load_dotenv()

chef_model = ChatOpenAI(
    model="gpt-5-nano",
    request_timeout=60,
)

chef_agent = create_agent(
    tools=[web_search],
    model=chef_model,
    system_prompt=CHEF_AGENT_PROMPT,
    response_format=RecipeResponse,
)

  
def stream_chef_agent(messages: List[AnyMessage], config: dict) -> Generator[str, None, None]:
    """Stream the chef agent response with structured JSON events"""
    
    for token, metadata in chef_agent.stream(
        {"messages": messages},
        stream_mode="messages",
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
                
                yield json.dumps({
                    "type": "tool_call",
                    "tool_call": {
                        "id": tool_id,
                        "name": tool_name,
                        "arguments": tool_args
                    }
                }) + "\n"
        
        # Stream tool responses
        if isinstance(token, ToolMessage):
            tool_call_id = getattr(token, 'tool_call_id', 'unknown')
            tool_name = getattr(token, 'name', 'unknown')
            content = getattr(token, 'content', '')
            
            yield json.dumps({
                "type": "tool_result",
                "tool_result": {
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": str(content) if content else ""
                }
            }) + "\n"
        
        # Stream content tokens
        if hasattr(token, 'content') and token.content and not (isinstance(token, AIMessage) and token.tool_calls):
            yield json.dumps({
                "type": "data",
                "data": token.content
            }) + "\n"

