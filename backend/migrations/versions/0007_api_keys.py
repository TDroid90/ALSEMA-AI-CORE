"""add API keys

Revision ID: 0007_api_keys
Revises: 0006_resource_owners
"""
from alembic import op
import sqlalchemy as sa

revision="0007_api_keys"; down_revision="0006_resource_owners"; branch_labels=None; depends_on=None

def upgrade() -> None:
    op.create_table("api_keys", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("owner_user_id", sa.Uuid(), nullable=False), sa.Column("name", sa.String(120), nullable=False), sa.Column("prefix", sa.String(32), nullable=False), sa.Column("secret_hash", sa.String(128), nullable=False), sa.Column("scopes", sa.Text(), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True), sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True), sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.ForeignKeyConstraint(["owner_user_id"],["users.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("prefix"),sa.UniqueConstraint("secret_hash")); op.create_index("ix_api_keys_owner_user_id","api_keys",["owner_user_id"])

def downgrade() -> None:
    op.drop_index("ix_api_keys_owner_user_id",table_name="api_keys"); op.drop_table("api_keys")
