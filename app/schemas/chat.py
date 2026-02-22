from pydantic import BaseModel, Field
from typing import Literal


class ThreadResponse(BaseModel):
    """Response schema for thread creation."""
    thread_id: str


class MessageContent(BaseModel):
    """Schema for message content (text or multimodal)."""
    type: Literal["text", "image_url"]
    text: str | None = None
    image_url: dict | None = None


class StreamChatRequest(BaseModel):
    """
    Request schema for streaming chat.
    Note: This is for documentation only - actual endpoint uses Form/File.
    """
    thread_id: str = Field(..., description="Unique conversation thread identifier")
    message: str = Field(..., description="Text message from the user")
    # image is handled separately via UploadFile
