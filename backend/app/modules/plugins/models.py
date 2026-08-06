from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.identity.models import Base


class Plugin(Base):
    __tablename__ = "plugins"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    version: Mapped[str] = mapped_column(String(50))
    manifest_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="disabled")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
