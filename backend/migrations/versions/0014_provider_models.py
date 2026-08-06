"""add provider model catalog

Revision ID: 0014_provider_models
Revises: 0013_rbac
"""
from alembic import op
import sqlalchemy as sa

revision = "0014_provider_models"
down_revision = "0013_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("provider_models", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("provider", sa.String(80), nullable=False), sa.Column("external_id", sa.String(255), nullable=False), sa.Column("display_name", sa.String(255), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("metadata_json", sa.Text(), nullable=False), sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("external_id"))
    op.create_index("ix_provider_models_provider", "provider_models", ["provider"])


def downgrade() -> None:
    op.drop_index("ix_provider_models_provider", table_name="provider_models")
    op.drop_table("provider_models")
