"""add machine-to-machine API key controls

Revision ID: 0021_machine_api_keys
Revises: 0020_social_publishers
"""

import sqlalchemy as sa
from alembic import op

revision = "0021_machine_api_keys"
down_revision = "0020_social_publishers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("api_keys", "owner_user_id", new_column_name="user_id")
    op.alter_column("api_keys", "prefix", new_column_name="key_prefix")
    op.alter_column("api_keys", "secret_hash", new_column_name="key_hash")
    op.add_column(
        "api_keys",
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.execute("ALTER INDEX ix_api_keys_owner_user_id RENAME TO ix_api_keys_user_id")


def downgrade() -> None:
    op.execute("ALTER INDEX ix_api_keys_user_id RENAME TO ix_api_keys_owner_user_id")
    op.drop_column("api_keys", "enabled")
    op.alter_column("api_keys", "key_hash", new_column_name="secret_hash")
    op.alter_column("api_keys", "key_prefix", new_column_name="prefix")
    op.alter_column("api_keys", "user_id", new_column_name="owner_user_id")
