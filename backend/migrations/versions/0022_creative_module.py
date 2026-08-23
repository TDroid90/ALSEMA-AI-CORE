"""add native creative operations module

Revision ID: 0022_creative_module
Revises: 0021_machine_api_keys
"""

import sqlalchemy as sa
from alembic import op

revision = "0022_creative_module"
down_revision = "0021_machine_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "creative_brands",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("profile_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_creative_brands_slug", "creative_brands", ["slug"], unique=True)
    op.create_table(
        "creative_catalog_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "brand_id",
            sa.Uuid(),
            sa.ForeignKey("creative_brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_key", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("category", sa.String(255), nullable=False, server_default=""),
        sa.Column("subcategory", sa.String(255), nullable=False, server_default=""),
        sa.Column("source", sa.String(80), nullable=False, server_default="import"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("brand_id", "source_key", name="uq_creative_catalog_brand_source"),
    )
    op.create_index("ix_creative_catalog_items_brand_id", "creative_catalog_items", ["brand_id"])
    op.create_index(
        "ix_creative_catalog_items_source_key", "creative_catalog_items", ["source_key"]
    )
    op.create_table(
        "creative_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(120), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("renderer", sa.String(40), nullable=False, server_default="layers"),
        sa.Column("document_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("key", "version", name="uq_creative_template_key_version"),
    )
    op.create_index("ix_creative_templates_key", "creative_templates", ["key"])
    op.create_table(
        "creative_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column(
            "brand_id",
            sa.Uuid(),
            sa.ForeignKey("creative_brands.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "catalog_item_id",
            sa.Uuid(),
            sa.ForeignKey("creative_catalog_items.id", ondelete="SET NULL"),
        ),
        sa.Column("task_id", sa.Uuid(), sa.ForeignKey("tasks.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(40), nullable=False, server_default="queued"),
        sa.Column("campaign", sa.String(80), nullable=False, server_default="producto"),
        sa.Column("format", sa.String(40), nullable=False, server_default="instagram_feed"),
        sa.Column("template_keys_json", sa.Text(), nullable=False, server_default='["A"]'),
        sa.Column("content_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("options_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("provider_plan_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("qa_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text()),
        sa.Column("approved_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("approval_comment", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_creative_jobs_owner_user_id", "creative_jobs", ["owner_user_id"])
    op.create_index("ix_creative_jobs_brand_id", "creative_jobs", ["brand_id"])
    op.create_index("ix_creative_jobs_status", "creative_jobs", ["status"])
    op.create_index("ix_creative_jobs_created_at", "creative_jobs", ["created_at"])
    op.create_table(
        "creative_assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("job_id", sa.Uuid(), sa.ForeignKey("creative_jobs.id", ondelete="CASCADE")),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("variant", sa.String(120)),
        sa.Column("storage_path", sa.String(600), nullable=False, unique=True),
        sa.Column("media_type", sa.String(120), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_creative_assets_job_id", "creative_assets", ["job_id"])
    op.create_index("ix_creative_assets_kind", "creative_assets", ["kind"])
    op.create_index("ix_creative_assets_sha256", "creative_assets", ["sha256"])
    permissions = [
        "creative.view",
        "creative.create",
        "creative.edit",
        "creative.generate",
        "creative.approve",
        "creative.export",
        "creative.manage_templates",
        "creative.manage_brands",
        "creative.manage_catalogs",
        "creative.manage_providers",
    ]
    for code in permissions:
        op.execute(
            sa.text(
                "INSERT INTO permissions (id, code, description) VALUES (gen_random_uuid(), :code, :description) ON CONFLICT (code) DO NOTHING"
            ).bindparams(code=code, description=f"Creative module permission: {code}")
        )


def downgrade() -> None:
    op.drop_table("creative_assets")
    op.drop_table("creative_jobs")
    op.drop_table("creative_templates")
    op.drop_table("creative_catalog_items")
    op.drop_table("creative_brands")
    op.execute("DELETE FROM permissions WHERE code LIKE 'creative.%'")
