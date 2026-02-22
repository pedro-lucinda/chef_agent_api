from langchain.tools import tool
from app.agents.chef_agent.agent import chef_agent
from langchain_core.messages import HumanMessage


@tool
def call_chef_agent(message: str) -> str: 
    """Call the chef agent to generate one recipe based on the user's ingredients and instructions."""
    response = chef_agent.invoke({"messages": [HumanMessage(content=message)]})
    
    # Return structured response if available, otherwise fall back to message content
    if response.get("structured_response"):
        return response["structured_response"].model_dump_json(indent=2)
    
    return response["messages"][-1].content