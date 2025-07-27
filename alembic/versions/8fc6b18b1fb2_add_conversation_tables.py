"""add conversation tables

Revision ID: 8fc6b18b1fb2
Revises: ae102fee8486
Create Date: 2025-07-27 08:09:46.414296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fc6b18b1fb2'
down_revision: Union[str, Sequence[str], None] = 'ae102fee8486'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "conversations",
        sa.Column("conversation_id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("status", sa.String(), nullable=True),
    )

    op.create_table(
        "messages",
        sa.Column("message_id", sa.UUID(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.UUID(),
            sa.ForeignKey("conversations.conversation_id"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("message_type", sa.String(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    op.create_table(
        "usage",
        sa.Column("usage_id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("file_uploads", sa.Integer(), nullable=True),
        sa.Column(
            "last_updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("usage")
    op.drop_table("messages")
    op.drop_table("conversations")
