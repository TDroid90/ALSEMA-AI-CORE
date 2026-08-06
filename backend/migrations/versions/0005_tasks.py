"""add durable tasks

Revision ID: 0005_tasks
Revises: 0004_agents
"""
from alembic import op
import sqlalchemy as sa
revision="0005_tasks";down_revision="0004_agents";branch_labels=None;depends_on=None
def upgrade() -> None:
    op.create_table("tasks",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("type",sa.String(120),nullable=False),sa.Column("status",sa.String(30),nullable=False),sa.Column("progress_current",sa.Integer(),nullable=False),sa.Column("progress_total",sa.Integer(),nullable=False),sa.Column("progress_message",sa.Text(),nullable=False),sa.Column("result",sa.Text(),nullable=True),sa.Column("error",sa.Text(),nullable=True),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.Column("started_at",sa.DateTime(timezone=True),nullable=True),sa.Column("completed_at",sa.DateTime(timezone=True),nullable=True),sa.PrimaryKeyConstraint("id"))
def downgrade() -> None: op.drop_table("tasks")
