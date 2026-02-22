from langchain.tools import tool
from tavily import TavilyClient
from typing import Dict, Any
from app.core.config import settings



tavily_client = TavilyClient(api_key=settings.tavily_api_key)


@tool
def web_search(text_query: str) -> Dict[str, Any]:
    """Search the web for recipes by text query"""
    return tavily_client.search(text_query)

