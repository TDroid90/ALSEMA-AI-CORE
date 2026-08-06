from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.modules.identity.models import User
from app.modules.memory.models import MemoryEntry
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


class MemoryInput(BaseModel):
    namespace: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=20000)
    scope: str = Field(default="user", pattern="^(user|conversation|agent|project|global)$")
    scope_key: str | None = Field(default=None, max_length=255)
    expires_at: datetime | None = None


@router.get("")
async def list_memory(namespace: str | None = None, query: str | None = None, scope: str | None = None, scope_key: str | None = None, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("memory:read"))) -> dict[str, object]:
    statement = select(MemoryEntry).where(or_(MemoryEntry.owner_user_id == user.id, MemoryEntry.scope == "global"), or_(MemoryEntry.expires_at.is_(None), MemoryEntry.expires_at > datetime.now(UTC))).order_by(MemoryEntry.created_at.desc())
    if namespace: statement = statement.where(MemoryEntry.namespace == namespace)
    if query: statement = statement.where(MemoryEntry.content.ilike(f"%{query}%"))
    if scope: statement = statement.where(MemoryEntry.scope == scope)
    if scope_key: statement = statement.where(MemoryEntry.scope_key == scope_key)
    items = (await session.scalars(statement.limit(100))).all()
    return {"items": [{"id": str(item.id), "namespace": item.namespace, "scope": item.scope, "scope_key": item.scope_key, "content": item.content, "source": item.source, "created_at": item.created_at.isoformat(), "expires_at": item.expires_at.isoformat() if item.expires_at else None} for item in items]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(payload: MemoryInput, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("memory:write"))) -> dict[str, str]:
    if payload.expires_at and payload.expires_at <= datetime.now(UTC): raise HTTPException(status_code=422, detail="La expiración debe ser futura.")
    if payload.scope == "global" and not user.is_system_admin: raise HTTPException(status_code=403, detail="Solo un administrador puede crear memoria global.")
    if payload.scope not in {"user", "global"} and not payload.scope_key: raise HTTPException(status_code=422, detail="El scope requiere scope_key.")
    item = MemoryEntry(owner_user_id=user.id, namespace=payload.namespace, scope=payload.scope, scope_key=payload.scope_key, content=payload.content, expires_at=payload.expires_at)
    session.add(item); await session.commit()
    return {"id": str(item.id)}


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("memory:write"))) -> None:
    item = await session.get(MemoryEntry, memory_id)
    if item is None or item.owner_user_id != user.id: raise HTTPException(status_code=404, detail="Memoria no encontrada.")
    await session.delete(item); await session.commit()
