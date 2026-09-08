"""add instanews social publication dispatches

Revision ID: 0023_instanews_social_dispatch
Revises: 0022_creative_module
"""

import sqlalchemy as sa
from alembic import op

revision = "0023_instanews_social_dispatch"
down_revision = "0022_creative_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instanews_social_dispatches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("news_id", sa.String(180), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("feed_image_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "facebook_publication_id",
            sa.Uuid(),
            sa.ForeignKey("plugin_facebook_publications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "instagram_publication_id",
            sa.Uuid(),
            sa.ForeignKey("plugin_instagram_publications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("news_id"),
    )
    op.create_index(
        "ix_instanews_social_dispatches_news_id",
        "instanews_social_dispatches",
        ["news_id"],
        unique=True,
    )
    op.create_index(
        "ix_instanews_social_dispatches_status",
        "instanews_social_dispatches",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_instanews_social_dispatches_status", table_name="instanews_social_dispatches")
    op.drop_index("ix_instanews_social_dispatches_news_id", table_name="instanews_social_dispatches")
    op.drop_table("instanews_social_dispatches")

