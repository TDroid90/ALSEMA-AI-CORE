from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class InstaNewsSocialDispatch(Base):
    __tablename__ = "instanews_social_dispatches"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    news_id: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    caption: Mapped[str] = mapped_column(Text)
    feed_image_url: Mapped[str] = mapped_column(Text)
    story_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    facebook_publication_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plugin_facebook_publications.id", ondelete="SET NULL"), nullable=True
    )
    instagram_publication_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plugin_instagram_publications.id", ondelete="SET NULL"), nullable=True
    )
    facebook_story_publication_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plugin_facebook_publications.id", ondelete="SET NULL"), nullable=True
    )
    instagram_story_publication_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plugin_instagram_publications.id", ondelete="SET NULL"), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
