import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from langchain.tools import tool
from tavily import TavilyClient
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

tavily_client = TavilyClient(api_key=settings.tavily_api_key)
_search_executor = ThreadPoolExecutor(max_workers=4)
WEB_SEARCH_TIMEOUT_SECONDS = 15


@tool
def web_search(text_query: str) -> Dict[str, Any]:
    """Search the web for recipes by text query."""
    future = _search_executor.submit(tavily_client.search, text_query)
    try:
        return future.result(timeout=WEB_SEARCH_TIMEOUT_SECONDS)
    except FuturesTimeoutError:
        logger.warning("web_search timed out after %s seconds", WEB_SEARCH_TIMEOUT_SECONDS)
        return {"error": "Search timed out. Please generate the recipe from your knowledge."}

