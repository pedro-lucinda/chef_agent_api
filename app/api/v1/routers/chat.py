import logging
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.dependencies.auth0 import get_current_user

logger = logging.getLogger(__name__)


class ThreadResponse(BaseModel):
    thread_id: str


router = APIRouter()


@router.post("/thread", response_model=ThreadResponse, dependencies=[Depends(get_current_user)])
def create_thread() -> ThreadResponse:
    """Create a new chat thread for the user."""
    thread_id = str(uuid4())
    logger.info(f"Created new chat thread: {thread_id}")
    return ThreadResponse(thread_id=thread_id)
