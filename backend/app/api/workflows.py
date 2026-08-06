import json
from datetime import UTC, datetime
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.config.settings import get_settings
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.modules.workflows.models import Workflow, WorkflowRun, WorkflowSchedule, WorkflowVersion
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


class Graph(BaseModel):
    nodes: list[dict[str, object]] = Field(min_length=2)
    edges: list[dict[str, str]] = Field(min_length=1)


class WorkflowInput(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    graph: Graph


class RunInput(BaseModel):
    input: dict[str, object] = Field(default_factory=dict)


class ApprovalInput(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    comment: str = Field(default="", max_length=2_000)


class ScheduleInput(BaseModel):
    run_at: datetime
    input: dict[str, object] = Field(default_factory=dict)


@router.get("")
async def list_workflows(session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> dict[str, object]:
    statement = select(Workflow).order_by(Workflow.created_at.desc())
    if not user.is_system_admin:
        statement = statement.where(Workflow.owner_user_id == user.id)
    workflows = (await session.scalars(statement)).all()
    return {"items": [{"id": str(workflow.id), "name": workflow.name, "description": workflow.description, "status": workflow.status, "created_at": workflow.created_at.isoformat()} for workflow in workflows]}


def validate_graph(graph: Graph) -> None:
    node_ids = [str(node.get("id", "")) for node in graph.nodes]
    if len(node_ids) != len(set(node_ids)) or any(not value for value in node_ids):
        raise HTTPException(status_code=422, detail="Los nodos requieren IDs únicos.")
    types = {str(node.get("type", "")) for node in graph.nodes}
    if "input" not in types or "output" not in types:
        raise HTTPException(status_code=422, detail="El grafo requiere nodos input y output.")
    supported_types = {
        "input",
        "output",
        "agent",
        "condition",
        "approval",
        "python",
        "transform",
        "file_read",
        "file_write",
        "http",
        "delay",
        "loop",
    }
    unknown_types = types - supported_types
    if unknown_types:
        raise HTTPException(status_code=422, detail=f"El grafo contiene tipos de nodo no registrados: {', '.join(sorted(unknown_types))}.")
    for node in graph.nodes:
        node_type = str(node.get("type", ""))
        if node_type == "agent" and not isinstance(node.get("agent_id"), str):
            raise HTTPException(status_code=422, detail="Todo nodo agent requiere agent_id.")
        if node_type == "condition" and not isinstance(node.get("field"), str):
            raise HTTPException(status_code=422, detail="Todo nodo condition requiere field.")
        if node_type == "python" and not isinstance(node.get("source"), str):
            raise HTTPException(status_code=422, detail="Todo nodo python requiere source.")
        if node_type in {"file_read", "file_write"} and not isinstance(node.get("path"), str):
            raise HTTPException(status_code=422, detail=f"Todo nodo {node_type} requiere path.")
        if node_type == "http" and not isinstance(node.get("url"), str):
            raise HTTPException(status_code=422, detail="Todo nodo http requiere url.")
        if node_type == "delay":
            seconds = node.get("seconds")
            if not isinstance(seconds, int) or isinstance(seconds, bool) or not 0 <= seconds <= 300:
                raise HTTPException(status_code=422, detail="Todo nodo delay requiere seconds entre 0 y 300.")
        if node_type == "loop":
            items_field = node.get("items_field")
            max_iterations = node.get("max_iterations", 100)
            if not isinstance(items_field, str) or not items_field:
                raise HTTPException(status_code=422, detail="Todo nodo loop requiere items_field.")
            if not isinstance(max_iterations, int) or isinstance(max_iterations, bool) or not 1 <= max_iterations <= 1000:
                raise HTTPException(status_code=422, detail="Todo nodo loop requiere max_iterations entre 1 y 1000.")
    for edge in graph.edges:
        if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
            raise HTTPException(status_code=422, detail="Una conexión referencia un nodo inexistente.")
    graph_map: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in graph.edges: graph_map[edge["from"]].append(edge["to"])
    visiting: set[str] = set(); visited: set[str] = set()
    def visit(node_id: str) -> None:
        if node_id in visiting: raise HTTPException(status_code=422, detail="El grafo no puede contener ciclos.")
        if node_id not in visited:
            visiting.add(node_id)
            for successor in graph_map[node_id]: visit(successor)
            visiting.remove(node_id); visited.add(node_id)
    for node_id in node_ids: visit(node_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(payload: WorkflowInput, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> dict[str, str]:
    validate_graph(payload.graph)
    workflow = Workflow(owner_user_id=user.id, name=payload.name, description=payload.description)
    session.add(workflow); await session.flush()
    version = WorkflowVersion(workflow_id=workflow.id, version_number=1, graph_json=payload.graph.model_dump_json())
    session.add(version); await session.commit()
    return {"id": str(workflow.id), "version_id": str(version.id)}


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    workflow = await session.get(Workflow, workflow_id)
    if workflow is None or (workflow.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Workflow no encontrado.")
    versions = (
        await session.scalars(
            select(WorkflowVersion)
            .where(WorkflowVersion.workflow_id == workflow.id)
            .order_by(WorkflowVersion.version_number.desc())
        )
    ).all()
    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "versions": [
            {
                "id": str(version.id),
                "number": version.version_number,
                "status": version.status,
                "graph": json.loads(version.graph_json),
            }
            for version in versions
        ],
    }


@router.post("/{workflow_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_version(workflow_id: UUID, payload: WorkflowInput, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> dict[str, str]:
    workflow = await session.get(Workflow, workflow_id)
    if workflow is None or workflow.owner_user_id != user.id: raise HTTPException(status_code=404, detail="Workflow no encontrado.")
    validate_graph(payload.graph)
    number = (await session.scalar(select(func.coalesce(func.max(WorkflowVersion.version_number), 0)).where(WorkflowVersion.workflow_id == workflow_id))) or 0
    version = WorkflowVersion(workflow_id=workflow_id, version_number=number + 1, graph_json=payload.graph.model_dump_json())
    session.add(version); await session.commit()
    return {"id": str(version.id), "version": str(version.version_number)}


@router.post("/{workflow_id}/versions/{version_id}/publish")
async def publish_workflow(workflow_id: UUID, version_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> dict[str, str]:
    workflow = await session.get(Workflow, workflow_id); version = await session.get(WorkflowVersion, version_id)
    if workflow is None or version is None or workflow.owner_user_id != user.id or version.workflow_id != workflow.id: raise HTTPException(status_code=404, detail="Versión no encontrada.")
    version.status = "published"; workflow.status = "active"
    await record_audit(session, user.id, "workflow.published", "workflow", str(workflow.id), {"version": version.version_number})
    await session.commit()
    return {"status": "published"}


@router.post("/{workflow_id}/versions/{version_id}/runs", status_code=status.HTTP_202_ACCEPTED)
async def run_workflow(workflow_id: UUID, version_id: UUID, payload: RunInput, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> dict[str, str]:
    workflow = await session.get(Workflow, workflow_id); version = await session.get(WorkflowVersion, version_id)
    if workflow is None or version is None or workflow.owner_user_id != user.id or version.workflow_id != workflow.id or version.status != "published": raise HTTPException(status_code=409, detail="Workflow publicado no encontrado.")
    run = WorkflowRun(workflow_version_id=version.id, owner_user_id=user.id, input_json=json.dumps(payload.input))
    session.add(run); await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url)); await pool.enqueue_job("run_workflow", str(run.id)); await pool.aclose()
    return {"run_id": str(run.id), "status": run.status}


@router.post("/{workflow_id}/versions/{version_id}/schedules", status_code=status.HTTP_201_CREATED)
async def schedule_workflow(
    workflow_id: UUID,
    version_id: UUID,
    payload: ScheduleInput,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    workflow = await session.get(Workflow, workflow_id)
    version = await session.get(WorkflowVersion, version_id)
    if workflow is None or version is None or workflow.owner_user_id != user.id or version.workflow_id != workflow.id or version.status != "published":
        raise HTTPException(status_code=409, detail="Workflow publicado no encontrado.")
    run_at = payload.run_at if payload.run_at.tzinfo else payload.run_at.replace(tzinfo=UTC)
    if run_at <= datetime.now(UTC):
        raise HTTPException(status_code=422, detail="La programación debe estar en el futuro.")
    schedule = WorkflowSchedule(workflow_version_id=version.id, owner_user_id=user.id, run_at=run_at, input_json=json.dumps(payload.input))
    session.add(schedule)
    await record_audit(session, user.id, "workflow.scheduled", "workflow_schedule", str(schedule.id), {"run_at": run_at.isoformat()})
    await session.commit()
    return {"schedule_id": str(schedule.id), "status": schedule.status}


@router.get("/runs/{run_id}")
async def get_run(run_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> dict[str, object]:
    run = await session.get(WorkflowRun, run_id)
    if run is None or run.owner_user_id != user.id: raise HTTPException(status_code=404, detail="Ejecución no encontrada.")
    return {"id": str(run.id), "status": run.status, "output": json.loads(run.output_json) if run.output_json else None, "error": run.error}


@router.post("/runs/{run_id}/approval", status_code=status.HTTP_202_ACCEPTED)
async def decide_approval(run_id: UUID, payload: ApprovalInput, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> dict[str, str]:
    run = await session.get(WorkflowRun, run_id)
    if run is None or (run.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Ejecución no encontrada.")
    if run.status != "waiting_approval":
        raise HTTPException(status_code=409, detail="La ejecución no está esperando una aprobación.")
    state = json.loads(run.output_json or "{}")
    state["approval"] = {"decision": payload.decision, "comment": payload.comment, "actor_id": str(user.id)}
    run.output_json = json.dumps(state, ensure_ascii=False)
    run.status = "queued"
    await record_audit(session, user.id, "workflow.approval_decided", "workflow_run", str(run.id), {"decision": payload.decision})
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("run_workflow", str(run.id))
    await pool.aclose()
    return {"run_id": str(run.id), "status": run.status}
