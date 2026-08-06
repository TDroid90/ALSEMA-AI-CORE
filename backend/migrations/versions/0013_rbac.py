"""add RBAC tables

Revision ID: 0013_rbac
Revises: 0012_plugins
"""
from alembic import op
import sqlalchemy as sa
revision="0013_rbac"; down_revision="0012_plugins"; branch_labels=None; depends_on=None
def upgrade() -> None:
    op.create_table("roles",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("slug",sa.String(80),nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("is_system_role",sa.Boolean(),nullable=False),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("slug"));op.create_table("permissions",sa.Column("id",sa.Uuid(),nullable=False),sa.Column("code",sa.String(120),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("code"));op.create_table("user_roles",sa.Column("user_id",sa.Uuid(),nullable=False),sa.Column("role_id",sa.Uuid(),nullable=False),sa.ForeignKeyConstraint(["user_id"],["users.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["role_id"],["roles.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("user_id","role_id"));op.create_table("role_permissions",sa.Column("role_id",sa.Uuid(),nullable=False),sa.Column("permission_id",sa.Uuid(),nullable=False),sa.ForeignKeyConstraint(["role_id"],["roles.id"],ondelete="CASCADE"),sa.ForeignKeyConstraint(["permission_id"],["permissions.id"],ondelete="CASCADE"),sa.PrimaryKeyConstraint("role_id","permission_id"))
def downgrade() -> None: op.drop_table("role_permissions");op.drop_table("user_roles");op.drop_table("permissions");op.drop_table("roles")
