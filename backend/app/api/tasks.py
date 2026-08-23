from datetime import UTC, datetime
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission, require_system_admin
from app.config.settings import get_settings
from app.modules.identity.models import User
from app.modules.tasks.models import Task
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class SleepTaskInput(BaseModel):
    seconds: int = Field(default=10, ge=2, le=60)


def serialize_task(task: Task) -> dict[str, object]:
    return {"id": str(task.id), "type": task.type, "status": task.status, "progress": {"current": task.progress_current, "total": task.progress_total, "message": task.progress_message}, "attempts": {"current": task.attempt_count, "maximum": task.max_attempts}, "result": task.result, "error": task.error, "created_at": task.created_at.isoformat()}


@router.get("")
async def list_tasks(session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("tasks:read"))) -> dict[str, object]:
    statement = select(Task).order_by(Task.created_at.desc()).limit(100)
    if not user.is_system_admin:
        statement = statement.where(Task.owner_user_id == user.id)
    return {"items": [serialize_task(task) for task in (await session.scalars(statement)).all()]}


@router.post("/smoke", status_code=status.HTTP_202_ACCEPTED)
async def create_smoke_task(session: AsyncSession = Depends(get_session), user: User = Depends(require_system_admin)) -> dict[str, str]:
    task = Task(type="system.smoke", owner_user_id=user.id)
    session.add(task); await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("run_smoke_task", str(task.id))
    await pool.aclose()
    return {"task_id": str(task.id), "status": task.status}


@router.post("/sleep", status_code=status.HTTP_202_ACCEPTED)
async def create_sleep_task(
    payload: SleepTaskInput,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_system_admin),
) -> dict[str, str]:
    task = Task(
        type="system.sleep",
        owner_user_id=user.id,
        result=str(payload.seconds),
        progress_total=payload.seconds,
        progress_message="En cola",
    )
    session.add(task)
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("run_sleep_task", str(task.id))
    await pool.aclose()
    return {"task_id": str(task.id), "status": task.status}


@router.get("/{task_id}")
async def get_task(task_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("tasks:read"))) -> dict[str, object]:
    task = await session.get(Task, task_id)
    if task is None or (task.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    return serialize_task(task)


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_system_admin)) -> dict[str, object]:
    task = await session.get(Task, task_id)
    if task is None or (task.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    if task.status == "queued":
        task.status = "cancelled"; task.progress_message = "Cancelada"; task.completed_at = datetime.now(UTC)
    elif task.status in {"running", "uploading", "processing"}:
        task.status = "cancelling"; task.progress_message = "Cancelación solicitada"
    else:
        raise HTTPException(status_code=409, detail="La tarea ya no puede cancelarse.")
    await session.commit()
    return serialize_task(task)


@router.post("/{task_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_task(task_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_system_admin)) -> dict[str, object]:
    original = await session.get(Task, task_id)
    if original is None or (original.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    if original.status not in {"failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Solo se pueden reintentar tareas fallidas o canceladas.")
    task = Task(type=original.type, owner_user_id=user.id, result=original.result, progress_message="Reintento en cola")
    session.add(task); await session.commit()
    job_name = {
        "system.smoke": "run_smoke_task",
        "system.sleep": "run_sleep_task",
        "provider.ollama.pull": "pull_ollama_model",
        "instagram.media.prepare": "prepare_instagram_media",
        "facebook.media.prepare": "prepare_facebook_media",
        "creative.generate": "generate_creative",
        "creative.import": "import_creativosur_data",
        "creative.cutout": "prepare_creative_cutout",
    }.get(task.type)
    if job_name is None:
        task.status = "failed"; task.error = "El tipo de tarea no admite reintento."; task.completed_at = datetime.now(UTC); await session.commit()
        raise HTTPException(status_code=409, detail="El tipo de tarea no admite reintento.")
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job(job_name, str(task.id)); await pool.aclose()
    return serialize_task(task)
