class Message(BaseModel):
    content: str
    role: Literal["user", "assistant"]