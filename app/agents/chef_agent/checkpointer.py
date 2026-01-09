"""
PostgreSQL checkpointer for LangGraph agent state persistence.
"""
import logging
from langgraph.checkpoint.postgres import PostgresSaver
from app.core.config import settings

logger = logging.getLogger(__name__)

_checkpointer_instance = None
_context_manager = None


def get_postgres_uri() -> str:
    """
    Convert async database URL to sync PostgreSQL URI for checkpointer.
    
    PostgresSaver requires a sync connection string (postgresql:// not postgresql+asyncpg://).
    """
    # Replace asyncpg driver with psycopg2 (sync)
    uri = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    return uri


def get_checkpointer() -> PostgresSaver:
    """
    Get or create PostgreSQL checkpointer singleton.
    
    Note: setup() creates necessary tables. Should be called once on initialization.
    PostgresSaver.from_conn_string() returns a context manager, so we need to enter it.
    """
    global _checkpointer_instance, _context_manager
    
    if _checkpointer_instance is None:
        uri = get_postgres_uri()
        # from_conn_string returns a context manager
        _context_manager = PostgresSaver.from_conn_string(uri)
        # Enter the context manager to get the actual checkpointer instance
        _checkpointer_instance = _context_manager.__enter__()
        
        # Setup tables on first use (idempotent)
        try:
            _checkpointer_instance.setup()
            logger.info("PostgreSQL checkpointer tables initialized")
        except Exception as e:
            logger.warning(f"Checkpointer setup warning: {e}")
            # Continue anyway - tables might already exist
    
    return _checkpointer_instance


# Create singleton instance
checkpointer = get_checkpointer()
