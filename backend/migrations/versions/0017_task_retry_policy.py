"""add task retry policy

Revision ID: 0017_task_retry_policy
Revises: 0016_agent_output_schema
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_task_retry_policy"
down_revision = "0016_agent_output_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tasks", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"))


def downgrade() -> None:
    op.drop_column("tasks", "max_attempts")
    op.drop_column("tasks", "attempt_count")
