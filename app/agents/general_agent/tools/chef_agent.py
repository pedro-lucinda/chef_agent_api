from langchain.tools import tool
from app.agents.chef_agent.agent import chef_agent
from langchain_core.messages import HumanMessage
from typing import List


@tool
def call_chef_agent(message: str) -> str: 
    """Call the chef agent subagent to generate a recipe based on the user's ingredients and instructions"""
    response = chef_agent.invoke({"messages": [HumanMessage(content=message)]})
    return response["messages"][-1].content