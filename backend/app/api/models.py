import json
from datetime import UTC, datetime

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.config.settings import get_settings
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.modules.providers.application import OllamaHealthService
from app.modules.providers.models import ProviderModel
from app.modules.tasks.models import Task
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class PullModelInput(BaseModel):
    name: str = Field(pattern=r"^[A-Za-z0-9._:/-]{1,255}$")


async def sync_ollama(session: AsyncSession) -> list[ProviderModel]:
    try:
        catalog = await OllamaHealthService(get_settings()).list_models()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Proveedor no disponible.") from exc
    existing = {model.external_id: model for model in (await session.scalars(select(ProviderModel).where(ProviderModel.provider == "ollama"))).all()}
    seen: set[str] = set()
    for item in catalog:
        external_id = str(item["external_id"])
        seen.add(external_id)
        record = existing.get(external_id)
        if record is None:
            record = ProviderModel(provider="ollama", external_id=external_id, display_name=str(item.get("display_name") or external_id))
            session.add(record)
        record.status = "available"
        record.metadata_json = json.dumps(item)
        record.last_seen_at = datetime.now(UTC)
    for external_id, record in existing.items():
        if external_id not in seen:
            record.status = "unavailable"
    await session.commit()
    return list(
        (await session.scalars(select(ProviderModel).order_by(ProviderModel.display_name))).all()
    )


@router.get("")
async def list_models(session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("models:read"))) -> dict[str, object]:
    models = (await session.scalars(select(ProviderModel).order_by(ProviderModel.display_name))).all()
    return {"items": [{"id": str(item.id), "provider": item.provider, "model": item.external_id, "name": item.display_name, "status": item.status, "metadata": json.loads(item.metadata_json), "last_seen_at": item.last_seen_at.isoformat() if item.last_seen_at else None} for item in models]}


@router.post("/sync")
async def sync_models(session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("providers:manage"))) -> dict[str, int]:
    models = await sync_ollama(session)
    await record_audit(session, user.id, "provider.models.synced", "provider", "ollama", {"count": len(models)})
    await session.commit()
    return {"count": len(models)}


@router.post("/pull", status_code=status.HTTP_202_ACCEPTED)
async def pull_model(payload: PullModelInput, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("providers:manage"))) -> dict[str, str]:
    task = Task(type="provider.ollama.pull", owner_user_id=user.id, result=payload.name, progress_message="En cola para descargar modelo")
    session.add(task)
    await record_audit(session, user.id, "provider.model.pull_requested", "model", payload.name)
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("pull_ollama_model", str(task.id))
    await pool.aclose()
    return {"task_id": str(task.id), "status": task.status}
