"""
Thread router - handles conversation thread endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.api.v1.dependencies.auth0 import get_current_user
from app.api.v1.dependencies.async_db_session import get_async_db
from app.models.user import User as UserModel
from app.models.thread import Thread as ThreadModel
from app.schemas.thread import ThreadCreate, ThreadOut
from app.schemas.message import MessageOut
from app.services.thread_service import ThreadService

router = APIRouter()


@router.post("/", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
async def create_thread(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> ThreadOut:
    """Create a new conversation thread for the current user."""
    thread = await ThreadService(db).create_thread(current_user.id)
    # Access messages while in async context to ensure they're loaded
    messages = thread.messages if hasattr(thread, 'messages') else []
    return ThreadOut(
        id=thread.id,
        user_id=thread.user_id,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        messages=[MessageOut.model_validate(msg) for msg in messages]
    )


@router.get("/", response_model=List[ThreadOut])
async def get_threads(
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> List[ThreadOut]:
    """Get all threads for the current user."""
    threads = await ThreadService(db).get_threads(current_user.id)
    return [
        ThreadOut(
            id=thread.id,
            user_id=thread.user_id,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            messages=[MessageOut.model_validate(msg) for msg in (thread.messages or [])]
        )
        for thread in threads
    ]


@router.get("/{thread_id}", response_model=ThreadOut)
async def get_thread(
    thread_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
) -> ThreadOut:
    """Get a specific thread by ID (must belong to current user)."""
    thread = await ThreadService(db).get_thread(thread_id, current_user.id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    # Access messages while in async context
    messages = thread.messages if hasattr(thread, 'messages') else []
    return ThreadOut(
        id=thread.id,
        user_id=thread.user_id,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        messages=[MessageOut.model_validate(msg) for msg in messages]
    )


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a thread (must belong to current user)."""
    deleted = await ThreadService(db).delete_thread(thread_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
