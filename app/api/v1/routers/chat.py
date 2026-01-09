"""
Chat router - handles streaming chat endpoints.

This router is kept thin, delegating business logic to ChatService.
"""
import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile

from fastapi.responses import StreamingResponse

from app.api.v1.dependencies.auth0 import get_current_user
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stream")
async def stream_chat(
    thread_id: str = Form(..., description="Unique conversation thread identifier"),
    message: str = Form(..., description="Text message from the user"),
    image: UploadFile | None = File(None, description="Optional image file (jpeg, png, webp, gif)"),
    user_language: str = Form("English", description="User's preferred response language"),
    _user = Depends(get_current_user)  # Auth check only
):
    """
    Stream the chef agent response.
    
    User must be authenticated. Accepts text message and optional image.
    
    - **thread_id**: Unique conversation thread identifier
    - **message**: Text message from the user
    - **image**: Optional image file (jpeg, png, webp, gif)
    - **user_language**: Preferred response language (default: English)
    """
    # Process image if provided
    image_base64, image_type = await chat_service.process_image(image)
    
    # Return streaming response
    return StreamingResponse(
        chat_service.stream_response(
            message=message,
            thread_id=thread_id,
            image_base64=image_base64,
            image_type=image_type,
            user_language=user_language
        ),
        media_type="text/event-stream"
    )
