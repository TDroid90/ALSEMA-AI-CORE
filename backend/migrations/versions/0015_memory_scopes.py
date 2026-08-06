"""add memory scopes

Revision ID: 0015_memory_scopes
Revises: 0014_provider_models
"""
from alembic import op
import sqlalchemy as sa

revision = "0015_memory_scopes"
down_revision = "0014_provider_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("memory_entries", sa.Column("scope", sa.String(40), nullable=False, server_default="user"))
    op.add_column("memory_entries", sa.Column("scope_key", sa.String(255), nullable=True))
    op.create_index("ix_memory_entries_scope", "memory_entries", ["scope"])
    op.create_index("ix_memory_entries_scope_key", "memory_entries", ["scope_key"])


def downgrade() -> None:
    op.drop_index("ix_memory_entries_scope_key", table_name="memory_entries")
    op.drop_index("ix_memory_entries_scope", table_name="memory_entries")
    op.drop_column("memory_entries", "scope_key")
    op.drop_column("memory_entries", "scope")
