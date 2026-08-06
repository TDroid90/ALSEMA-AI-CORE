from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    type: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=1)
    progress_message: Mapped[str] = mapped_column(Text, default="En cola")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
