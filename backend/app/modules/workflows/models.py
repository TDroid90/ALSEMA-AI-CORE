from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class Workflow(Base):
    __tablename__ = "workflows"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkflowVersion(Base):
    __tablename__ = "workflow_versions"
    __table_args__ = (UniqueConstraint("workflow_id", "version_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("workflows.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    graph_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workflow_version_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_versions.id", ondelete="RESTRICT"), index=True)
    owner_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowSchedule(Base):
    __tablename__ = "workflow_schedules"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workflow_version_id: Mapped[UUID] = mapped_column(ForeignKey("workflow_versions.id", ondelete="CASCADE"), index=True)
    owner_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
