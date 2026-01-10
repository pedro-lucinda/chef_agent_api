"""convert_thread_and_message_ids_to_uuid

Revision ID: 9e7df46889a5
Revises: 3d1a47267ba5
Create Date: 2026-01-10 03:36:29.951686

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9e7df46889a5'
down_revision: Union[str, None] = '3d1a47267ba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - convert thread and message IDs to UUID."""
    # Drop foreign key constraint first
    op.drop_constraint('messages_thread_id_fkey', 'messages', type_='foreignkey')
    
    # Drop existing tables (for fresh start - data will be lost)
    op.drop_table('messages')
    op.drop_table('threads')
    
    # Recreate threads table with UUID
    op.create_table('threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_threads_id'), 'threads', ['id'], unique=False)
    op.create_index(op.f('ix_threads_user_id'), 'threads', ['user_id'], unique=False)
    
    # Recreate messages table with UUID
    op.create_table('messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_thread_id'), 'messages', ['thread_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - convert back to INTEGER."""
    # Drop tables
    op.drop_table('messages')
    op.drop_table('threads')
    
    # Recreate with INTEGER (data will be lost)
    op.create_table('threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_threads_id'), 'threads', ['id'], unique=False)
    op.create_index(op.f('ix_threads_user_id'), 'threads', ['user_id'], unique=False)
    
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('thread_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_thread_id'), 'messages', ['thread_id'], unique=False)
