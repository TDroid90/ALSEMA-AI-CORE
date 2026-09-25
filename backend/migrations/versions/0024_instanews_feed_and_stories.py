"""publish instanews feed and stories

Revision ID: 0024_instanews_feed_and_stories
Revises: 0023_instanews_social_dispatch
"""

import sqlalchemy as sa
from alembic import op

revision = "0024_instanews_feed_and_stories"
down_revision = "0023_instanews_social_dispatch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("instanews_social_dispatches", sa.Column("story_image_url", sa.Text(), nullable=True))
    op.add_column(
        "instanews_social_dispatches",
        sa.Column("facebook_story_publication_id", sa.Uuid(), sa.ForeignKey("plugin_facebook_publications.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "instanews_social_dispatches",
        sa.Column("instagram_story_publication_id", sa.Uuid(), sa.ForeignKey("plugin_instagram_publications.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("instanews_social_dispatches", "instagram_story_publication_id")
    op.drop_column("instanews_social_dispatches", "facebook_story_publication_id")
    op.drop_column("instanews_social_dispatches", "story_image_url")
