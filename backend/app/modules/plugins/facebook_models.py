from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class FacebookAccount(Base):
    __tablename__ = "plugin_facebook_accounts"
    __table_args__ = (UniqueConstraint("account_label", name="uq_plugin_facebook_account_label"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_label: Mapped[str] = mapped_column(String(120))
    app_id: Mapped[str] = mapped_column(String(120))
    app_secret_encrypted: Mapped[str] = mapped_column(Text)
    page_id: Mapped[str] = mapped_column(String(64), index=True)
    page_access_token_encrypted: Mapped[str] = mapped_column(Text)
    api_version: Mapped[str] = mapped_column(String(20), default="v26.0")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_publish: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    last_connection_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_connection_profile_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_connection_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FacebookPublication(Base):
    __tablename__ = "plugin_facebook_publications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("plugin_facebook_accounts.id", ondelete="RESTRICT"), index=True)
    requested_by_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    placement: Mapped[str] = mapped_column(String(20), default="feed")
    caption: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    photo_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    post_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sanitized_response_json: Mapped[str] = mapped_column(Text, default="{}")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
