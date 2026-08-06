"""add memory entries

Revision ID: 0009_memory_entries
Revises: 0008_audit_events
"""
from alembic import op
import sqlalchemy as sa
revision="0009_memory_entries"; down_revision="0008_audit_events"; branch_labels=None; depends_on=None
def upgrade() -> None:
    op.create_table("memory_entries",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("owner_user_id",sa.Uuid(),nullable=False),sa.Column("namespace",sa.String(160),nullable=False),sa.Column("content",sa.Text(),nullable=False),sa.Column("source",sa.String(80),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=True),sa.ForeignKeyConstraint(["owner_user_id"],["users.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("id")); op.create_index("ix_memory_entries_owner_user_id","memory_entries",["owner_user_id"]); op.create_index("ix_memory_entries_namespace","memory_entries",["namespace"]); op.create_index("ix_memory_entries_created_at","memory_entries",["created_at"])
def downgrade() -> None: op.drop_table("memory_entries")
