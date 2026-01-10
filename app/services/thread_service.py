from app.models.thread import Thread
from app.models.message import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID


class ThreadService:
    """Service layer for thread operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_thread(self, user_id: int) -> Thread:
        """Create a new thread for a user."""
        thread = Thread(user_id=user_id)
        self.db.add(thread)
        await self.db.commit()
        await self.db.refresh(thread)
        # Eagerly load messages (empty list for new thread)
        stmt = select(Thread).options(selectinload(Thread.messages)).where(Thread.id == thread.id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_thread(self, thread_id: UUID, user_id: Optional[int] = None) -> Optional[Thread]:
        """
        Get a thread by ID, optionally filtered by user_id.
        
        Args:
            thread_id: Thread ID
            user_id: Optional user ID to verify ownership
            
        Returns:
            Thread if found and accessible, None otherwise
        """
        stmt = select(Thread).options(selectinload(Thread.messages)).where(Thread.id == thread_id)
        if user_id:
            stmt = stmt.where(Thread.user_id == user_id)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_threads(self, user_id: int) -> List[Thread]:
        """Get all threads for a user."""
        stmt = (
            select(Thread)
            .options(selectinload(Thread.messages))
            .where(Thread.user_id == user_id)
            .order_by(Thread.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_thread(self, thread_id: UUID, user_id: int) -> bool:
        """
        Delete a thread if it belongs to the user.
        
        Args:
            thread_id: Thread ID to delete
            user_id: User ID to verify ownership
            
        Returns:
            True if deleted, False if not found or not owned by user
        """
        thread = await self.get_thread(thread_id, user_id)
        if not thread:
            return False
        
        await self.db.delete(thread)
        await self.db.commit()
        return True
