"""add instagram publisher plugin persistence

Revision ID: 0019_instagram_publisher
Revises: 0018_workflow_schedules
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_instagram_publisher"
down_revision = "0018_workflow_schedules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plugin_instagram_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_label", sa.String(120), nullable=False),
        sa.Column("app_id", sa.String(120), nullable=False),
        sa.Column("app_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("instagram_user_id", sa.String(64), nullable=False),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("api_version", sa.String(20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("last_connection_status", sa.String(30), nullable=True),
        sa.Column("last_connection_profile_json", sa.Text(), nullable=True),
        sa.Column("last_connection_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_label", name="uq_plugin_instagram_account_label"),
    )
    op.create_index("ix_plugin_instagram_accounts_instagram_user_id", "plugin_instagram_accounts", ["instagram_user_id"])
    op.create_index("ix_plugin_instagram_accounts_created_by_user_id", "plugin_instagram_accounts", ["created_by_user_id"])
    op.create_table(
        "plugin_instagram_publications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("container_id", sa.String(128), nullable=True),
        sa.Column("media_id", sa.String(128), nullable=True),
        sa.Column("sanitized_response_json", sa.Text(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("container_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["plugin_instagram_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("container_id"),
    )
    op.create_index("ix_plugin_instagram_publications_account_id", "plugin_instagram_publications", ["account_id"])
    op.create_index("ix_plugin_instagram_publications_requested_by_user_id", "plugin_instagram_publications", ["requested_by_user_id"])
    op.create_index("ix_plugin_instagram_publications_status", "plugin_instagram_publications", ["status"])
    op.create_index("ix_plugin_instagram_publications_created_at", "plugin_instagram_publications", ["created_at"])


def downgrade() -> None:
    op.drop_table("plugin_instagram_publications")
    op.drop_table("plugin_instagram_accounts")
