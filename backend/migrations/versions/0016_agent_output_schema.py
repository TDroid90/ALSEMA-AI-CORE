"""add structured agent output schema

Revision ID: 0016_agent_output_schema
Revises: 0015_memory_scopes
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_agent_output_schema"
down_revision = "0015_memory_scopes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_versions", sa.Column("output_schema_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_versions", "output_schema_json")
