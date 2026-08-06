import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import AuditEvent


async def record_audit(session: AsyncSession, actor_user_id: UUID | None, action: str, target_type: str, target_id: str | None = None, metadata: dict[str, object] | None = None) -> None:
    session.add(AuditEvent(actor_user_id=actor_user_id, action=action, target_type=target_type, target_id=target_id, metadata_json=json.dumps(metadata or {})))
