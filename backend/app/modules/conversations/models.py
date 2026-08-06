from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(240), default="Nueva conversación")
    model: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text, default="")
    sequence: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="complete")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
