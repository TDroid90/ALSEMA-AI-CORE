from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    key: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentVersion(Base):
    __tablename__ = "agent_versions"
    __table_args__ = (UniqueConstraint("agent_id", "version_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    system_prompt: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(255))
    temperature: Mapped[str] = mapped_column(String(20), default="0.7")
    output_schema_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
