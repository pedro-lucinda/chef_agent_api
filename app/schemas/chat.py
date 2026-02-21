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


class ResumeDecision(BaseModel):
    """One HITL decision (approve / reject / edit)."""
    type: str = Field(..., description="One of: approve, reject, edit")
    message: str | None = Field(None, description="Required for reject: feedback message")
    edited_action: dict | None = Field(None, description="For edit: { name, args }")


class ChatResumeBody(BaseModel):
    """Body for POST /resume after an interrupt."""
    thread_id: str = Field(..., description="Same thread_id as the stream that was interrupted")
    decisions: list[ResumeDecision] = Field(..., description="Decisions in same order as action_requests")
    user_language: str = Field("English", description="User's preferred language")
