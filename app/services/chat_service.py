import base64
import json
import logging
from typing import AsyncGenerator, Generator
from uuid import UUID

from fastapi import UploadFile
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.general_agent.agent import stream_general_agent
from app.agents.general_agent.schemas import GeneralAgentContext
from app.services.message_service import MessageService

logger = logging.getLogger(__name__)


class ChatService:
    """Service layer for chat operations."""

    @staticmethod
    def create_message_content(
        text: str, 
        image_base64: str | None = None, 
        image_type: str = "image/jpeg"
    ) -> str | list:
        """
        Create message content with text and optional image.
        
        Args:
            text: The text message content
            image_base64: Optional base64-encoded image
            image_type: MIME type of the image
            
        Returns:
            String for text-only, or list for multimodal content
        """
        if image_base64:
            return [
                {"type": "text", "text": text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_type};base64,{image_base64}"}
                }
            ]
        return text

    @staticmethod
    async def process_image(image: UploadFile | None) -> tuple[str | None, str]:
        """
        Process uploaded image file to base64.
        
        Args:
            image: Optional uploaded image file
            
        Returns:
            Tuple of (base64_string or None, mime_type)
        """
        if not image or not image.filename:
            return None, "image/jpeg"
        
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_type = image.content_type or "image/jpeg"
        
        logger.debug(f"Processed image: {image.filename}, type: {image_type}")
        return image_base64, image_type

    @staticmethod
    def build_context(user_language: str = "English") -> GeneralAgentContext:
        """
        Build the agent context.
        
        Args:
            user_language: User's preferred language
            
        Returns:
            GeneralAgentContext instance
        """
        return GeneralAgentContext(user_language=user_language)

    @staticmethod
    def build_config(thread_id: str) -> dict:
        """
        Build the agent config.
        
        Args:
            thread_id: Conversation thread identifier
            
        Returns:
            Config dictionary for the agent
        """
        return {"configurable": {"thread_id": thread_id}}

    def stream_response(
        self,
        message: str,
        thread_id: str,
        image_base64: str | None = None,
        image_type: str = "image/jpeg",
        user_language: str = "English"
    ) -> Generator[str, None, None]:
        """
        Stream the agent response.
        
        Args:
            message: User's text message
            thread_id: Conversation thread identifier
            image_base64: Optional base64-encoded image
            image_type: MIME type of the image
            user_language: User's preferred language
            
        Yields:
            Response tokens from the agent
        """
        content = self.create_message_content(message, image_base64, image_type)
        config = self.build_config(thread_id)
        context = self.build_context(user_language)
        
        langchain_messages = [HumanMessage(content=content)]
        
        yield from stream_general_agent(langchain_messages, config, context)

    async def stream_with_persistence(
        self,
        message: str,
        thread_id: str,
        user_id: int,
        db: AsyncSession,
        image_base64: str | None = None,
        image_type: str = "image/jpeg",
        user_language: str = "English"
    ) -> AsyncGenerator[str, None]:
        """
        Stream the agent response and persist messages to database.
        
        Note: The PostgresSaver checkpointer handles agent memory/history.
        We only save messages to the database for frontend display purposes.
        
        Args:
            message: User's text message
            thread_id: Conversation thread identifier (string)
            user_id: User ID for message ownership
            db: Database session
            image_base64: Optional base64-encoded image
            image_type: MIME type of the image
            user_language: User's preferred language
            
        Yields:
            Response tokens from the agent
        """
        thread_uuid = UUID(thread_id)
        message_service = MessageService(db)
        
        # Save user message to database (for frontend display)
        await message_service.create_message(
            thread_id=thread_uuid,
            content=message,
            role="user",
            user_id=user_id
        )
        
        # Create current message content (with optional image)
        # Note: Checkpointer handles history - we only pass the new message
        current_content = self.create_message_content(message, image_base64, image_type)
        current_message = HumanMessage(content=current_content)
        
        # Build config and context
        config = self.build_config(thread_id)
        context = self.build_context(user_language)
        
        # Stream and collect response
        full_response_parts: list[str] = []
        
        for chunk in stream_general_agent([current_message], config, context):
            yield chunk
            
            # Extract text content from data events
            try:
                parsed = json.loads(chunk.strip())
                if parsed.get("type") == "data" and parsed.get("data"):
                    full_response_parts.append(parsed["data"])
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Save assistant message after stream completes (for frontend display)
        if full_response_parts:
            full_response = "".join(full_response_parts)
            await message_service.create_message(
                thread_id=thread_uuid,
                content=full_response,
                role="assistant",
                user_id=user_id
            )
            logger.debug(f"Saved assistant message: {len(full_response)} chars")


# Singleton instance
chat_service = ChatService()
