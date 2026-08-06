"""add plugin registry

Revision ID: 0012_plugins
Revises: 0011_workflow_runs
"""
from alembic import op
import sqlalchemy as sa
revision="0012_plugins"; down_revision="0011_workflow_runs"; branch_labels=None; depends_on=None
def upgrade() -> None: op.create_table("plugins",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("version",sa.String(50),nullable=False),sa.Column("manifest_json",sa.Text(),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("name"))
def downgrade() -> None: op.drop_table("plugins")
