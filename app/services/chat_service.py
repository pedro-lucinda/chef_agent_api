import asyncio
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
from app.agents.general_agent.tools.save_recipe_tool import _normalize_recipe_payload
from app.services.message_service import MessageService
from app.utils.recipe_utils import normalize_recipe_times

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
    def build_context(
        user_language: str = "English",
        user_id: int | None = None,
    ) -> GeneralAgentContext:
        """
        Build the agent context.

        Args:
            user_language: User's preferred language
            user_id: Current user ID (for save_recipe tool)

        Returns:
            GeneralAgentContext instance
        """
        return GeneralAgentContext(user_language=user_language, user_id=user_id)

    @staticmethod
    def build_config(thread_id: str, user_id: int | None = None) -> dict:
        """
        Build the agent config.

        Args:
            thread_id: Conversation thread identifier
            user_id: Current user ID (for save_recipe tool)

        Returns:
            Config dictionary for the agent
        """
        config: dict = {"configurable": {"thread_id": thread_id}}
        if user_id is not None:
            config["configurable"]["user_id"] = user_id
        return config

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
        
        current_content = self.create_message_content(message, image_base64, image_type)
        current_message = HumanMessage(content=current_content)
        
        # Build config and context (user_id for save_recipe tool)
        config = self.build_config(thread_id, user_id=user_id)
        context = self.build_context(user_language, user_id=user_id)

        def _status_event(message: str) -> str:
            """SSE event for frontend loading/status display (only when creating a recipe)."""
            return "data: " + json.dumps({"type": "status", "status": message}) + "\n\n"

        # Stream and collect response (async iteration so each chunk is sent immediately)
        full_response_parts: list[str] = []
        recipes_for_message: list[dict] = []  # persisted with message for UI on refresh
        sync_stream = stream_general_agent([current_message], config, context)
        loop = asyncio.get_event_loop()

        def _next_or_none(gen):
            try:
                return next(gen)
            except StopIteration:
                return None

        def _is_recipe_json(text: str) -> bool:
            """True if text is (or looks like) call_chef_agent JSON so we don't save it as message content."""
            if not text:
                return False
            s = text.strip()
            if s.startswith('{"recipes"') or s.startswith("{\"recipes\""):
                return True
            if not s.startswith("{"):
                return False
            try:
                data = json.loads(text)
                return isinstance(data, dict) and "recipes" in data
            except (json.JSONDecodeError, TypeError):
                return False

        while True:
            chunk = await loop.run_in_executor(None, _next_or_none, sync_stream)
            if chunk is None:
                break

            # When we see call_chef_agent tool_call, emit status so frontend can show "Creating recipe..." loading state
            try:
                line = chunk.strip()
                if line.startswith("data: "):
                    json_str = line[6:]
                    parsed = json.loads(json_str)
                    if parsed.get("type") == "tool_call":
                        tc = parsed.get("tool_call") or {}
                        if tc.get("name") == "call_chef_agent":
                            yield _status_event("Creating your recipe...")
                    if parsed.get("type") == "tool_result":
                        tr = parsed.get("tool_result") or {}
                        name = tr.get("name")
                        # Do not send present_recipes_for_save / save_recipe results to client
                        if name in ("present_recipes_for_save", "save_recipe"):
                            continue
                        if name == "call_chef_agent" and tr.get("content"):
                            try:
                                data = json.loads(tr["content"])
                                raw_recipes = (data.get("recipes") or [])[:1]
                                recipes_for_message = [_normalize_recipe_payload(r) for r in raw_recipes]
                            except (json.JSONDecodeError, TypeError, KeyError):
                                raw_recipes = []
                                recipes_for_message = []
                            if recipes_for_message:
                                # Only emit the recipe event; stream text only when the assistant sends real data events
                                recipe_event = "data: " + json.dumps({"type": "recipe", "recipes": recipes_for_message}) + "\n\n"
                                yield recipe_event
                            continue  # Do not forward raw call_chef_agent tool_result to client
            except (json.JSONDecodeError, AttributeError):
                pass

            yield chunk

            # Extract text content from data events (skip recipe JSON so user never sees it in saved content)
            try:
                line = chunk.strip()
                if line.startswith("data: "):
                    json_str = line[6:]
                    parsed = json.loads(json_str)
                    if parsed.get("type") == "data" and parsed.get("data"):
                        data_content = parsed["data"]
                        if not _is_recipe_json(data_content):
                            full_response_parts.append(data_content)
            except (json.JSONDecodeError, AttributeError):
                pass

        # Save assistant message (and recipe data for UI on refresh); only use streamed content, or recipe name as minimal fallback
        full_response = "".join(full_response_parts) if full_response_parts else None
        if not full_response and recipes_for_message:
            full_response = (recipes_for_message[0].get("name") or "Recipe").strip() or None
        if full_response:
            await message_service.create_message(
                thread_id=thread_uuid,
                content=full_response,
                role="assistant",
                user_id=user_id,
                recipe_data=recipes_for_message if recipes_for_message else None,
            )
            logger.debug(f"Saved assistant message: {len(full_response)} chars")


# Singleton instance
chat_service = ChatService()
