from pydantic import BaseModel, Field


class GeneralAgentContext(BaseModel):
    user_language: str = Field(default="English")
