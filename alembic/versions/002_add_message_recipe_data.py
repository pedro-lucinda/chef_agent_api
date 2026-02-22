"""add message recipe_data column

Revision ID: 002
Revises: 3d1a47267ba5
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "3d1a47267ba5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("recipe_data", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "recipe_data")
