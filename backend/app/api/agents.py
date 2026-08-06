import json
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from jsonschema import Draft202012Validator, SchemaError, ValidationError
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.config.settings import get_settings
from app.modules.agents.models import Agent, AgentVersion
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class AgentInput(BaseModel):
    key: str = Field(pattern="^[a-z0-9-]{3,120}$")
    name: str = Field(min_length=1, max_length=160)
    description: str = ""
    system_prompt: str = Field(min_length=1)
    model: str
    temperature: float = Field(default=0.7, ge=0, le=2)
    output_schema: dict[str, object] | None = None


class AgentRunInput(BaseModel):
    input: str = Field(min_length=1, max_length=100000)


class AgentDuplicateInput(BaseModel):
    key: str = Field(pattern="^[a-z0-9-]{3,120}$")
    name: str = Field(min_length=1, max_length=160)


def validate_output_schema(schema: dict[str, object] | None) -> None:
    if schema is None:
        return
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise HTTPException(status_code=422, detail="El esquema de salida no es JSON Schema válido.") from exc


@router.get("")
async def list_agents(session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("agents:read"))) -> dict[str, object]:
    statement = select(Agent).order_by(Agent.created_at.desc())
    if not user.is_system_admin:
        statement = statement.where(Agent.owner_user_id == user.id)
    agents = (await session.scalars(statement.where(Agent.status != "archived"))).all()
    return {"items": [{"id": str(agent.id), "key": agent.key, "name": agent.name, "status": agent.status} for agent in agents]}


@router.get("/{agent_id}")
async def get_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("agents:read")),
) -> dict[str, object]:
    agent = await session.get(Agent, agent_id)
    if agent is None or (agent.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    versions = (
        await session.scalars(
            select(AgentVersion)
            .where(AgentVersion.agent_id == agent.id)
            .order_by(AgentVersion.version_number.desc())
        )
    ).all()
    return {
        "id": str(agent.id),
        "key": agent.key,
        "name": agent.name,
        "description": agent.description,
        "status": agent.status,
        "versions": [
            {
                "id": str(version.id),
                "number": version.version_number,
                "model": version.model,
                "temperature": float(version.temperature),
                "status": version.status,
                "output_schema": json.loads(version.output_schema_json)
                if version.output_schema_json
                else None,
            }
            for version in versions
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentInput, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("agents:write"))) -> dict[str, str]:
    if await session.scalar(select(Agent).where(Agent.key == payload.key)):
        raise HTTPException(status_code=409, detail="La clave de agente ya existe.")
    validate_output_schema(payload.output_schema)
    agent = Agent(key=payload.key, name=payload.name, description=payload.description, owner_user_id=user.id)
    session.add(agent)
    await session.flush()
    session.add(AgentVersion(agent_id=agent.id, version_number=1, system_prompt=payload.system_prompt, model=payload.model, temperature=str(payload.temperature), output_schema_json=json.dumps(payload.output_schema) if payload.output_schema else None))
    await record_audit(session, user.id, "agent.created", "agent", str(agent.id), {"key": agent.key})
    await session.commit()
    return {"id": str(agent.id), "version": "1"}


@router.post("/{agent_id}/versions", status_code=status.HTTP_201_CREATED)
async def add_version(agent_id: UUID, payload: AgentInput, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("agents:write"))) -> dict[str, str]:
    agent = await session.get(Agent, agent_id)
    if agent is None or (agent.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    validate_output_schema(payload.output_schema)
    number = (await session.scalar(select(func.coalesce(func.max(AgentVersion.version_number), 0)).where(AgentVersion.agent_id == agent_id))) or 0
    version = AgentVersion(agent_id=agent_id, version_number=number + 1, system_prompt=payload.system_prompt, model=payload.model, temperature=str(payload.temperature), output_schema_json=json.dumps(payload.output_schema) if payload.output_schema else None)
    session.add(version)
    await record_audit(session, user.id, "agent.version_created", "agent", str(agent.id), {"version": version.version_number})
    await session.commit()
    return {"id": str(version.id), "version": str(version.version_number)}


@router.post("/{agent_id}/duplicate", status_code=status.HTTP_201_CREATED)
async def duplicate_agent(agent_id: UUID, payload: AgentDuplicateInput, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("agents:write"))) -> dict[str, str]:
    source = await session.get(Agent, agent_id)
    if source is None or (source.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    if await session.scalar(select(Agent).where(Agent.key == payload.key)):
        raise HTTPException(status_code=409, detail="La clave de agente ya existe.")
    version = await session.scalar(select(AgentVersion).where(AgentVersion.agent_id == source.id).order_by(AgentVersion.version_number.desc()))
    if version is None:
        raise HTTPException(status_code=409, detail="El agente no tiene versiones para duplicar.")
    duplicate = Agent(key=payload.key, name=payload.name, description=source.description, owner_user_id=user.id)
    session.add(duplicate); await session.flush()
    session.add(AgentVersion(agent_id=duplicate.id, version_number=1, system_prompt=version.system_prompt, model=version.model, temperature=version.temperature, output_schema_json=version.output_schema_json))
    await record_audit(session, user.id, "agent.duplicated", "agent", str(duplicate.id), {"source_agent_id": str(source.id)})
    await session.commit()
    return {"id": str(duplicate.id), "version": "1"}


@router.post("/{agent_id}/versions/{version_id}/publish")
async def publish_version(agent_id: UUID, version_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("agents:publish"))) -> dict[str, str]:
    version = await session.get(AgentVersion, version_id)
    agent = await session.get(Agent, agent_id)
    if version is None or agent is None or version.agent_id != agent_id or (agent.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Versión no encontrada.")
    version.status = "published"; agent.status = "active"
    await record_audit(session, user.id, "agent.published", "agent", str(agent.id), {"version": version.version_number})
    await session.commit()
    return {"status": "published"}


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("agents:publish")),
) -> dict[str, str]:
    agent = await session.get(Agent, agent_id)
    if agent is None or (agent.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    if agent.status != "active":
        raise HTTPException(status_code=409, detail="El agente no está activo.")
    agent.status = "inactive"
    await record_audit(session, user.id, "agent.deactivated", "agent", str(agent.id))
    await session.commit()
    return {"status": agent.status}


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("agents:write")),
) -> None:
    agent = await session.get(Agent, agent_id)
    if agent is None or (agent.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    if agent.status == "archived":
        raise HTTPException(status_code=409, detail="El agente ya está archivado.")
    agent.status = "archived"
    await record_audit(session, user.id, "agent.archived", "agent", str(agent.id))
    await session.commit()


@router.post("/{agent_id}/restore")
async def restore_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("agents:write")),
) -> dict[str, str]:
    agent = await session.get(Agent, agent_id)
    if agent is None or (agent.owner_user_id != user.id and not user.is_system_admin):
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    if agent.status != "archived":
        raise HTTPException(status_code=409, detail="El agente no está archivado.")
    agent.status = "inactive"
    await record_audit(session, user.id, "agent.restored", "agent", str(agent.id))
    await session.commit()
    return {"status": agent.status}


@router.post("/{agent_id}/run")
async def run_agent(agent_id: UUID, payload: AgentRunInput, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("agents:read"))) -> dict[str, object]:
    agent = await session.get(Agent, agent_id)
    if agent is None or (agent.owner_user_id != user.id and not user.is_system_admin): raise HTTPException(status_code=404, detail="Agente no encontrado.")
    if agent.status != "active":
        raise HTTPException(status_code=409, detail="El agente está inactivo.")
    version = await session.scalar(select(AgentVersion).where(AgentVersion.agent_id == agent_id, AgentVersion.status == "published").order_by(AgentVersion.version_number.desc()))
    if version is None: raise HTTPException(status_code=409, detail="El agente no tiene una versión publicada.")
    body = {"model": version.model, "messages": [{"role": "system", "content": version.system_prompt}, {"role": "user", "content": payload.input}], "stream": False, "options": {"temperature": float(version.temperature)}}
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{str(get_settings().ollama_base_url).rstrip('/')}/api/chat", json=body); response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Proveedor no disponible.") from exc
    output = response.json().get("message", {}).get("content", "")
    if version.output_schema_json:
        try:
            parsed = json.loads(output)
            schema = json.loads(version.output_schema_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="El agente no devolvió JSON válido para su esquema de salida.") from exc
        try:
            Draft202012Validator(schema).validate(parsed)
        except (SchemaError, ValidationError) as exc:
            raise HTTPException(status_code=422, detail="La salida del agente no cumple el esquema declarado.") from exc
        return {"agent_id": str(agent.id), "version": version.version_number, "output": parsed}
    return {"agent_id": str(agent.id), "version": version.version_number, "output": output}
