from app.models.message import Message
from app.models.thread import Thread
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID


class MessageService:
    """Service layer for message operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self, 
        thread_id: UUID, 
        content: str, 
        role: str,
        user_id: int
    ) -> Optional[Message]:
        """
        Create a new message in a thread.
        
        Args:
            thread_id: Thread ID
            content: Message content
            role: Message role ("user" or "assistant")
            user_id: User ID to verify thread ownership
            
        Returns:
            Created message if thread exists and belongs to user, None otherwise
        """
        # Verify thread exists and belongs to user
        thread = await self._verify_thread_ownership(thread_id, user_id)
        if not thread:
            return None
        
        message = Message(
            thread_id=thread_id,
            content=content,
            role=role
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_messages(
        self, 
        thread_id: UUID, 
        user_id: int
    ) -> List[Message]:
        """
        Get all messages for a thread.
        
        Args:
            thread_id: Thread ID
            user_id: User ID to verify thread ownership
            
        Returns:
            List of messages if thread exists and belongs to user, empty list otherwise
        """
        # Verify thread ownership
        thread = await self._verify_thread_ownership(thread_id, user_id)
        if not thread:
            return []
        
        stmt = select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_message(
        self, 
        message_id: UUID, 
        user_id: int
    ) -> Optional[Message]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: Message ID
            user_id: User ID to verify thread ownership
            
        Returns:
            Message if found and thread belongs to user, None otherwise
        """
        stmt = select(Message).where(Message.id == message_id)
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()
        
        if not message:
            return None
        
        # Verify thread ownership
        thread = await self._verify_thread_ownership(message.thread_id, user_id)
        if not thread:
            return None
        
        return message

    async def delete_message(
        self, 
        message_id: UUID, 
        user_id: int
    ) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: Message ID to delete
            user_id: User ID to verify thread ownership
            
        Returns:
            True if deleted, False if not found or not owned by user
        """
        message = await self.get_message(message_id, user_id)
        if not message:
            return False
        
        await self.db.delete(message)
        await self.db.commit()
        return True

    async def _verify_thread_ownership(
        self, 
        thread_id: UUID, 
        user_id: int
    ) -> Optional[Thread]:
        """
        Verify that a thread exists and belongs to the user.
        
        Args:
            thread_id: Thread ID
            user_id: User ID
            
        Returns:
            Thread if found and belongs to user, None otherwise
        """
        stmt = select(Thread).where(
            Thread.id == thread_id,
            Thread.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
