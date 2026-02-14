"""
Chat router - handles streaming chat endpoints.

This router is kept thin, delegating business logic to ChatService.
"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth0 import get_current_user
from app.api.v1.dependencies.async_db_session import get_async_db
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("/stream")
async def stream_chat(
    thread_id: str = Form(..., description="Unique conversation thread identifier"),
    message: str = Form(..., description="Text message from the user"),
    image: UploadFile | None = File(None, description="Optional image file (jpeg, png, webp, gif)"),
    user_language: str = Form("English", description="User's preferred response language"),
    _user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> StreamingResponse:
    """
    Stream the chef agent response.
    
    User must be authenticated. Accepts text message and optional image.
    Messages are automatically saved to the database.
    
    - **thread_id**: Unique conversation thread identifier
    - **message**: Text message from the user
    - **image**: Optional image file (jpeg, png, webp, gif)
    - **user_language**: Preferred response language (default: English)
    """
    # Process image if provided
    image_base64, image_type = await chat_service.process_image(image)

    # Stream with message persistence
    return StreamingResponse(
        chat_service.stream_with_persistence(
            message=message,
            thread_id=thread_id,
            user_id=_user.id,
            db=db,
            image_base64=image_base64,
            image_type=image_type,
            user_language=user_language
        ),
        media_type="text/event-stream"
    )
