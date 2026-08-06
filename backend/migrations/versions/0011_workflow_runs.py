"""add workflow runs

Revision ID: 0011_workflow_runs
Revises: 0010_workflows
"""
from alembic import op
import sqlalchemy as sa
revision="0011_workflow_runs"; down_revision="0010_workflows"; branch_labels=None; depends_on=None
def upgrade() -> None:
    op.create_table("workflow_runs",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("workflow_version_id",sa.Uuid(),nullable=False),sa.Column("owner_user_id",sa.Uuid(),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("input_json",sa.Text(),nullable=False),sa.Column("output_json",sa.Text(),nullable=True),sa.Column("error",sa.Text(),nullable=True),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("completed_at",sa.DateTime(timezone=True),nullable=True),sa.ForeignKeyConstraint(["workflow_version_id"],["workflow_versions.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["owner_user_id"],["users.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("id"));op.create_index("ix_workflow_runs_workflow_version_id","workflow_runs",["workflow_version_id"]);op.create_index("ix_workflow_runs_owner_user_id","workflow_runs",["owner_user_id"])
def downgrade() -> None: op.drop_table("workflow_runs")
