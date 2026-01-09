import base64
import logging
from typing import Generator

from fastapi import UploadFile
from langchain_core.messages import HumanMessage

from app.services.agents.chef_agent.agent import stream_chef_agent
from app.services.agents.chef_agent.schemas import ChefAgentContext

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
    def build_context(user_language: str = "English") -> ChefAgentContext:
        """
        Build the agent context.
        
        Args:
            user_language: User's preferred language
            
        Returns:
            ChefAgentContext instance
        """
        return ChefAgentContext(user_language=user_language)

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
        
        yield from stream_chef_agent(langchain_messages, config, context)


# Singleton instance
chat_service = ChatService()
