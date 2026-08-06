from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    namespace: Mapped[str] = mapped_column(String(160), index=True)
    scope: Mapped[str] = mapped_column(String(40), default="user", index=True)
    scope_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
