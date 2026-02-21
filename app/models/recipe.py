from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db_config.base import Base


class Recipe(Base):
    """
    Recipe model.

    ingredients (JSONB): list of {"name": str, "quantity": str}.
    instructions (JSONB): list of {
        "step_number": int,
        "description": str,
        "time_minutes": int,
        "chef_tip": str | null (optional)
    }.
    """
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    prep_time = Column(Integer, nullable=False)
    cook_time = Column(Integer, nullable=False)
    total_time = Column(Integer, nullable=False)
    servings = Column(Integer, nullable=False)
    difficulty = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    ingredients = Column(JSONB, nullable=False)  # [{"name": str, "quantity": str}, ...]
    instructions = Column(JSONB, nullable=False)  # [{"step_number": int, "description": str, "time_minutes": int, "chef_tip": str|null}, ...]
    tags = Column(JSONB, nullable=False)  # [str, ...]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="recipes")