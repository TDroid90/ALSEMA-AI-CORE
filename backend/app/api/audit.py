import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.modules.identity.models import AuditEvent, User
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/audit-events", tags=["audit"])


@router.get("")
async def list_audit_events(
    action: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("system:admin")),
) -> dict[str, object]:
    statement = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    if action:
        statement = statement.where(AuditEvent.action == action)
    events = (await session.scalars(statement)).all()
    return {"items": [{"id": str(event.id), "actor_user_id": str(event.actor_user_id) if event.actor_user_id else None, "action": event.action, "target_type": event.target_type, "target_id": event.target_id, "outcome": event.outcome, "metadata": json.loads(event.metadata_json), "created_at": event.created_at.isoformat()} for event in events]}
