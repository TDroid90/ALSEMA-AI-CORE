from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class ProviderModel(Base):
    __tablename__ = "provider_models"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    external_id: Mapped[str] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="available")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
