"""
Message router - handles message endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.api.v1.dependencies.auth0 import get_current_user
from app.api.v1.dependencies.async_db_session import get_async_db
from app.models.user import User as UserModel
from app.schemas.message import MessageCreate, MessageOut
from app.services.message_service import MessageService

router = APIRouter()


@router.post("/", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def create_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> MessageOut:
    """
    Create a new message in a thread.
    
    The thread must belong to the current user.
    """
    created_message = await MessageService(db).create_message(
        thread_id=message.thread_id,
        content=message.content,
        role=message.role,
        user_id=current_user.id
    )
    
    if not created_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found or you don't have access to it"
        )
    
    return MessageOut.model_validate(created_message)


@router.get("/thread/{thread_id}", response_model=List[MessageOut])
async def get_messages(
    thread_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> List[MessageOut]:
    """
    Get all messages for a thread.
    
    The thread must belong to the current user.
    """
    messages = await MessageService(db).get_messages(thread_id, current_user.id)
    return [MessageOut.model_validate(msg) for msg in messages]


@router.get("/{message_id}", response_model=MessageOut)
async def get_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> MessageOut:
    """
    Get a specific message by ID.
    
    The message's thread must belong to the current user.
    """
    message = await MessageService(db).get_message(message_id, current_user.id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or you don't have access to it"
        )
    return MessageOut.model_validate(message)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete a message.
    
    The message's thread must belong to the current user.
    """
    deleted = await MessageService(db).delete_message(message_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or you don't have access to it"
        )
