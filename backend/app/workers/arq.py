from datetime import UTC, datetime
from typing import Any

from arq import cron
from arq.connections import RedisSettings, create_pool
from sqlalchemy import select

from app.config.settings import get_settings
from app.modules.tasks.models import Task
from app.modules.workflows.models import WorkflowRun, WorkflowSchedule
from app.shared.database import SessionFactory
from app.workers.jobs import (
    prepare_instagram_media,
    publish_instagram_media,
    pull_ollama_model,
    run_sleep_task,
    run_smoke_task,
    run_workflow,
)


def recoverable_task_job(task_type: str) -> str | None:
    return {
        "system.smoke": "run_smoke_task",
        "system.sleep": "run_sleep_task",
        "instagram.media.prepare": "prepare_instagram_media",
    }.get(task_type)


async def recover_interrupted_work(redis: Any) -> None:
    task_jobs: list[tuple[str, str]] = []
    workflow_runs: list[str] = []
    async with SessionFactory() as session:
        tasks = (
            await session.scalars(
                select(Task).where(
                    Task.status.in_({"running", "uploading", "processing", "publishing", "cancelling"})
                )
            )
        ).all()
        for task in tasks:
            if task.status == "cancelling":
                task.status = "cancelled"
                task.progress_message = "Cancelada durante el reinicio del worker"
                task.completed_at = datetime.now(UTC)
                continue
            job_name = recoverable_task_job(task.type)
            if job_name is None:
                task.status = "failed"
                task.error = "El worker se reinició durante la ejecución; reintente la tarea."
                task.completed_at = datetime.now(UTC)
                continue
            task.status = "queued"
            task.progress_message = "Recuperada después del reinicio del worker"
            task_jobs.append((job_name, str(task.id)))
        runs = (await session.scalars(select(WorkflowRun).where(WorkflowRun.status == "running"))).all()
        for run in runs:
            run.status = "queued"
            run.error = None
            workflow_runs.append(str(run.id))
        await session.commit()
    for job_name, task_id in task_jobs:
        await redis.enqueue_job(job_name, task_id)
    for run_id in workflow_runs:
        await redis.enqueue_job("run_workflow", run_id)


async def dispatch_due_schedules(ctx: dict[str, Any]) -> None:
    run_ids: list[str] = []
    async with SessionFactory() as session:
        schedules = (
            await session.scalars(
                select(WorkflowSchedule).where(
                    WorkflowSchedule.status == "scheduled",
                    WorkflowSchedule.run_at <= datetime.now(UTC),
                )
            )
        ).all()
        for schedule in schedules:
            run = WorkflowRun(
                workflow_version_id=schedule.workflow_version_id,
                owner_user_id=schedule.owner_user_id,
                input_json=schedule.input_json,
            )
            session.add(run)
            await session.flush()
            schedule.status = "dispatched"
            run_ids.append(str(run.id))
        await session.commit()
    for run_id in run_ids:
        await ctx["redis"].enqueue_job("run_workflow", run_id)


async def heartbeat(ctx: dict[str, Any]) -> None:
    await ctx["redis"].set("aas:worker:heartbeat", datetime.now(UTC).isoformat(), ex=30)
async def startup(ctx: dict[str, Any]) -> None:
    ctx["redis"] = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await recover_interrupted_work(ctx["redis"])
    await heartbeat(ctx)
class WorkerSettings:
    functions = [
        run_smoke_task,
        run_sleep_task,
        run_workflow,
        pull_ollama_model,
        prepare_instagram_media,
        publish_instagram_media,
    ]
    cron_jobs = [cron(heartbeat, second={0, 10, 20, 30, 40, 50}), cron(dispatch_due_schedules, second={0, 10, 20, 30, 40, 50})]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
