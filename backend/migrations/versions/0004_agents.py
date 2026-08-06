"""add agents

Revision ID: 0004_agents
Revises: 0003_conversations
"""
from alembic import op
import sqlalchemy as sa

revision="0004_agents"; down_revision="0003_conversations"; branch_labels=None; depends_on=None
def upgrade() -> None:
    op.create_table("agents",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("key",sa.String(120),nullable=False),sa.Column("name",sa.String(160),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("status",sa.String(20),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("key"))
    op.create_table("agent_versions",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("agent_id",sa.Uuid(),nullable=False),sa.Column("version_number",sa.Integer(),nullable=False),sa.Column("system_prompt",sa.Text(),nullable=False),sa.Column("model",sa.String(255),nullable=False),sa.Column("temperature",sa.String(20),nullable=False),sa.Column("status",sa.String(20),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["agent_id"],["agents.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("agent_id","version_number"))
def downgrade() -> None:
    op.drop_table("agent_versions");op.drop_table("agents")
