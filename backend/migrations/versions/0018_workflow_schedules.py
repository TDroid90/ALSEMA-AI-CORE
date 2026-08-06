"""add workflow schedules

Revision ID: 0018_workflow_schedules
Revises: 0017_task_retry_policy
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_workflow_schedules"
down_revision = "0017_task_retry_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workflow_version_id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workflow_version_id"], ["workflow_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_schedules_run_at", "workflow_schedules", ["run_at"])
    op.create_index("ix_workflow_schedules_workflow_version_id", "workflow_schedules", ["workflow_version_id"])
    op.create_index("ix_workflow_schedules_owner_user_id", "workflow_schedules", ["owner_user_id"])


def downgrade() -> None:
    op.drop_table("workflow_schedules")
