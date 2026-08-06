import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.config.settings import get_settings
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.modules.plugins.models import Plugin
from app.modules.plugins.runtime import PluginRuntimeViolation, execution_runtime
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])


class Manifest(BaseModel):
    name: str = Field(pattern="^[a-z0-9-]{3,120}$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
    core_version: str = Field(default=">=0.1.0", max_length=100)
    description: str = Field(default="", max_length=2000)
    entrypoint: str = Field(default="", max_length=255)
    capabilities: list[str] = Field(default_factory=list)
    tools: list[dict[str, object]] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class PythonPluginExecution(BaseModel):
    source: str = Field(min_length=1, max_length=20_000)


def validate_manifest(payload: Manifest) -> None:
    for tool in payload.tools:
        key = tool.get("key")
        risk = tool.get("risk")
        if not isinstance(key, str) or not key.startswith(f"{payload.name}."):
            raise HTTPException(status_code=422, detail="Cada herramienta debe usar una clave namespaced del plugin.")
        if risk not in {"read_only", "bounded_write", "external_write", "code_execution", "destructive"}:
            raise HTTPException(status_code=422, detail="Cada herramienta debe declarar un nivel de riesgo válido.")
    if any(permission in {"process.execute", "secrets.read"} for permission in payload.permissions):
        raise HTTPException(status_code=422, detail="Permisos críticos requieren una integración de runtime dedicada.")


@router.get("")
async def list_plugins(session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("plugins:manage"))) -> dict[str, object]:
    items = (await session.scalars(select(Plugin).order_by(Plugin.name))).all()
    return {"items": [{"id": str(item.id), "name": item.name, "version": item.version, "status": item.status, "manifest": json.loads(item.manifest_json)} for item in items]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_plugin(payload: Manifest, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("plugins:manage"))) -> dict[str, str]:
    if await session.scalar(select(Plugin).where(Plugin.name == payload.name)): raise HTTPException(status_code=409, detail="Plugin ya registrado.")
    validate_manifest(payload)
    plugin = Plugin(name=payload.name, version=payload.version, manifest_json=payload.model_dump_json())
    session.add(plugin); await record_audit(session, user.id, "plugin.registered", "plugin", payload.name, {"version": payload.version}); await session.commit()
    return {"id": str(plugin.id), "status": plugin.status}


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("plugins:manage"))) -> dict[str, str]:
    plugin = await session.get(Plugin, plugin_id)
    if plugin is None: raise HTTPException(status_code=404, detail="Plugin no encontrado.")
    manifest = Manifest.model_validate(json.loads(plugin.manifest_json))
    validate_manifest(manifest)
    plugin.status = "enabled"; await record_audit(session, user.id, "plugin.enabled", "plugin", str(plugin.id)); await session.commit()
    return {"status": plugin.status}


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("plugins:manage"))) -> dict[str, str]:
    plugin = await session.get(Plugin, plugin_id)
    if plugin is None: raise HTTPException(status_code=404, detail="Plugin no encontrado.")
    plugin.status = "disabled"; await record_audit(session, user.id, "plugin.disabled", "plugin", str(plugin.id)); await session.commit()
    return {"status": plugin.status}


@router.get("/{plugin_id}/health")
async def plugin_health(plugin_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("plugins:manage"))) -> dict[str, str]:
    plugin = await session.get(Plugin, plugin_id)
    if plugin is None: raise HTTPException(status_code=404, detail="Plugin no encontrado.")
    return {"status": "healthy" if plugin.status == "enabled" else "disabled", "plugin_status": plugin.status}


@router.post("/{plugin_id}/execute/python")
async def execute_python_plugin(plugin_id: UUID, payload: PythonPluginExecution, session: AsyncSession = Depends(get_session), user: User = Depends(require_permission("plugins:manage"))) -> dict[str, object]:
    plugin = await session.get(Plugin, plugin_id)
    if plugin is None or plugin.status != "enabled":
        raise HTTPException(status_code=409, detail="El plugin debe estar habilitado.")
    manifest = Manifest.model_validate(json.loads(plugin.manifest_json))
    if "python.execute" not in manifest.capabilities:
        raise HTTPException(status_code=403, detail="El plugin no declara ejecución Python.")
    try:
        result = await execution_runtime(get_settings()).execute_python(payload.source)
    except PluginRuntimeViolation as exc:
        await record_audit(session, user.id, "plugin.execution.rejected", "plugin", str(plugin.id), {"reason": str(exc)})
        await session.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await record_audit(session, user.id, "plugin.execution.completed", "plugin", str(plugin.id), {"exit_code": result.exit_code, "duration_ms": result.duration_ms})
    await session.commit()
    return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code, "duration_ms": result.duration_ms, "runtime": get_settings().plugin_runtime_mode}
