"""add audit events

Revision ID: 0008_audit_events
Revises: 0007_api_keys
"""
from alembic import op
import sqlalchemy as sa

revision="0008_audit_events"; down_revision="0007_api_keys"; branch_labels=None; depends_on=None

def upgrade() -> None:
    op.create_table("audit_events",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("actor_user_id",sa.Uuid(),nullable=True),sa.Column("action",sa.String(120),nullable=False),sa.Column("target_type",sa.String(80),nullable=False),sa.Column("target_id",sa.String(64),nullable=True),sa.Column("outcome",sa.String(30),nullable=False),sa.Column("metadata_json",sa.Text(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),sa.ForeignKeyConstraint(["actor_user_id"],["users.id"],ondelete="SET NULL"),sa.PrimaryKeyConstraint("id")); op.create_index("ix_audit_events_actor_user_id","audit_events",["actor_user_id"]); op.create_index("ix_audit_events_action","audit_events",["action"]); op.create_index("ix_audit_events_created_at","audit_events",["created_at"])

def downgrade() -> None:
    op.drop_table("audit_events")
