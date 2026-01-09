from pydantic import BaseModel, Field


class ChefAgentContext(BaseModel):
    user_language: str = Field(default="English")
