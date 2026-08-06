"""add Facebook publisher and social placements

Revision ID: 0020_social_publishers
Revises: 0019_instagram_publisher
"""

import sqlalchemy as sa
from alembic import op

revision = "0020_social_publishers"
down_revision = "0019_instagram_publisher"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plugin_instagram_accounts", sa.Column("auto_publish", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("plugin_instagram_publications", sa.Column("placement", sa.String(length=20), nullable=False, server_default="feed"))
    op.create_table(
        "plugin_facebook_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_label", sa.String(length=120), nullable=False),
        sa.Column("app_id", sa.String(length=120), nullable=False),
        sa.Column("app_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("page_id", sa.String(length=64), nullable=False),
        sa.Column("page_access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("api_version", sa.String(length=20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("auto_publish", sa.Boolean(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("last_connection_status", sa.String(length=30), nullable=True),
        sa.Column("last_connection_profile_json", sa.Text(), nullable=True),
        sa.Column("last_connection_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_label", name="uq_plugin_facebook_account_label"),
    )
    op.create_index("ix_plugin_facebook_accounts_page_id", "plugin_facebook_accounts", ["page_id"])
    op.create_index("ix_plugin_facebook_accounts_created_by_user_id", "plugin_facebook_accounts", ["created_by_user_id"])
    op.create_table(
        "plugin_facebook_publications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("placement", sa.String(length=20), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("photo_id", sa.String(length=128), nullable=True),
        sa.Column("post_id", sa.String(length=128), nullable=True),
        sa.Column("sanitized_response_json", sa.Text(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["plugin_facebook_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plugin_facebook_publications_account_id", "plugin_facebook_publications", ["account_id"])
    op.create_index("ix_plugin_facebook_publications_requested_by_user_id", "plugin_facebook_publications", ["requested_by_user_id"])
    op.create_index("ix_plugin_facebook_publications_status", "plugin_facebook_publications", ["status"])
    op.create_index("ix_plugin_facebook_publications_created_at", "plugin_facebook_publications", ["created_at"])


def downgrade() -> None:
    op.drop_table("plugin_facebook_publications")
    op.drop_table("plugin_facebook_accounts")
    op.drop_column("plugin_instagram_publications", "placement")
    op.drop_column("plugin_instagram_accounts", "auto_publish")
