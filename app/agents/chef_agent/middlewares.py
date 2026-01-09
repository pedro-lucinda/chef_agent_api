from app.agents.chef_agent.prompt import CHEF_AGENT_PROMPT
from langchain.agents.middleware import dynamic_prompt, ModelRequest


@dynamic_prompt
def _user_language_prompt(request: ModelRequest) -> str:
    """Generate system prompt based on user language."""
    user_language = request.runtime.context.user_language
    base_prompt = CHEF_AGENT_PROMPT

    if user_language != "English":
        return f"{base_prompt} Only respond in {user_language}."
    return base_prompt
