"""add conversations and messages

Revision ID: 0003_conversations
Revises: 0002_refresh_tokens
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_conversations"
down_revision = "0002_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("conversations", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("title", sa.String(240), nullable=False), sa.Column("model", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.PrimaryKeyConstraint("id"))
    op.create_table("messages", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("conversation_id", sa.Uuid(), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("sequence", sa.Integer(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
