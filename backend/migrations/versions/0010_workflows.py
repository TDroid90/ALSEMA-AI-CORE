"""add workflows

Revision ID: 0010_workflows
Revises: 0009_memory_entries
"""
from alembic import op
import sqlalchemy as sa
revision="0010_workflows"; down_revision="0009_memory_entries"; branch_labels=None; depends_on=None
def upgrade() -> None:
    op.create_table("workflows",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("owner_user_id",sa.Uuid(),nullable=False),sa.Column("name",sa.String(160),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["owner_user_id"],["users.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("id")); op.create_index("ix_workflows_owner_user_id","workflows",["owner_user_id"]); op.create_table("workflow_versions",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("workflow_id",sa.Uuid(),nullable=False),sa.Column("version_number",sa.Integer(),nullable=False),sa.Column("graph_json",sa.Text(),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["workflow_id"],["workflows.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("workflow_id","version_number")); op.create_index("ix_workflow_versions_workflow_id","workflow_versions",["workflow_id"])
def downgrade() -> None: op.drop_table("workflow_versions"); op.drop_table("workflows")
