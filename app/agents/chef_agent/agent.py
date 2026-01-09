from dotenv import load_dotenv
from langchain.agents import create_agent
from app.services.agents.chef_agent.tools.web_search_tool import web_search, web_search_image
from app.services.agents.chef_agent.prompt import CHEF_AGENT_PROMPT
from app.services.agents.chef_agent.schemas import ChefAgentContext
from app.services.agents.chef_agent.middlewares import _user_language_prompt
from app.services.agents.chef_agent.checkpointer import checkpointer
from langchain_core.messages import HumanMessage, AnyMessage
from typing import List, Generator

load_dotenv()


chef_agent = create_agent(
    tools=[web_search, web_search_image],
    model="gpt-5-nano",
    system_prompt=CHEF_AGENT_PROMPT,
    checkpointer=checkpointer,
    context_schema=ChefAgentContext,
    middleware=[_user_language_prompt],
)

  
def stream_chef_agent(messages: List[AnyMessage], config: dict, context: ChefAgentContext) -> Generator[str, None, None]:
    """Stream the chef agent response"""
    
    for token, metadata in chef_agent.stream(
        {"messages": messages},
        stream_mode="messages",
        config=config,
        context=context
    ):
        if hasattr(token, 'content') and token.content:
            yield token.content

