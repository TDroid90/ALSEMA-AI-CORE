"""scope user-owned resources

Revision ID: 0006_resource_owners
Revises: 0005_tasks
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_resource_owners"
down_revision = "0005_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("conversations", "agents", "tasks"):
        op.add_column(table, sa.Column("owner_user_id", sa.Uuid(), nullable=True))
        op.create_foreign_key(f"fk_{table}_owner_user", table, "users", ["owner_user_id"], ["id"], ondelete="SET NULL")
        op.create_index(f"ix_{table}_owner_user_id", table, ["owner_user_id"])


def downgrade() -> None:
    for table in ("tasks", "agents", "conversations"):
        op.drop_index(f"ix_{table}_owner_user_id", table_name=table)
        op.drop_constraint(f"fk_{table}_owner_user", table, type_="foreignkey")
        op.drop_column(table, "owner_user_id")
