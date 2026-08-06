import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.config.settings import get_settings
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.modules.tools.filesystem import SandboxFilesystem, SandboxViolation
from app.modules.tools.python_restricted import RestrictedPythonViolation, execute_restricted_python
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


class FilePathInput(BaseModel):
    path: str = Field(min_length=1, max_length=512)


class FileWriteInput(FilePathInput):
    content: str = Field(max_length=1_000_000)


class HttpRequestInput(BaseModel):
    url: str = Field(min_length=8, max_length=2048)
    method: str = Field(default="GET", pattern="^(GET|HEAD|POST)$")
    body: str | None = Field(default=None, max_length=100_000)


class PythonExecutionInput(BaseModel):
    source: str = Field(min_length=1, max_length=20_000)


def filesystem() -> SandboxFilesystem:
    return SandboxFilesystem(Path(get_settings().tool_sandbox_root))


def validate_http_destination(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Solo se permiten URLs HTTPS sin credenciales embebidas.")
    settings = get_settings()
    hostname = parsed.hostname.lower()
    if hostname not in settings.allowed_http_hosts:
        raise HTTPException(status_code=403, detail="El host no está permitido por la política HTTP.")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(hostname, None)}
        if any(ipaddress.ip_address(address).is_private or ipaddress.ip_address(address).is_loopback or ipaddress.ip_address(address).is_link_local for address in addresses):
            raise HTTPException(status_code=403, detail="El destino resuelve a una red privada o local.")
    except socket.gaierror as exc:
        raise HTTPException(status_code=422, detail="No se pudo resolver el host permitido.") from exc
    return url


@router.post("/files/read")
async def read_file(payload: FilePathInput, user: User = Depends(require_permission("tools:execute"))) -> dict[str, str]:
    try:
        return {"path": payload.path, "content": filesystem().read_text(payload.path)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.") from exc
    except (SandboxViolation, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=422, detail="Ruta o contenido no permitido.") from exc


@router.post("/files/write", status_code=status.HTTP_201_CREATED)
async def write_file(
    payload: FileWriteInput,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("tools:execute")),
) -> dict[str, str]:
    try:
        filesystem().write_text(payload.path, payload.content)
    except SandboxViolation as exc:
        raise HTTPException(status_code=422, detail="Ruta fuera del sandbox permitido.") from exc
    await record_audit(session, user.id, "tool.file.write", "file", payload.path)
    await session.commit()
    return {"path": payload.path, "status": "written"}


@router.post("/http")
async def http_request(
    payload: HttpRequestInput,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("tools:execute")),
) -> dict[str, object]:
    url = validate_http_destination(payload.url)
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, follow_redirects=False) as client:
            response = await client.request(payload.method, url, content=payload.body)
            content = response.content[:settings.http_max_response_bytes]
    except httpx.HTTPError as exc:
        await record_audit(session, user.id, "tool.http.failed", "url", url, {"method": payload.method})
        await session.commit()
        raise HTTPException(status_code=502, detail="La solicitud HTTP falló.") from exc
    await record_audit(session, user.id, "tool.http.executed", "url", url, {"method": payload.method, "status_code": response.status_code})
    await session.commit()
    return {"status_code": response.status_code, "content_type": response.headers.get("content-type", ""), "body": content.decode("utf-8", errors="replace"), "truncated": len(response.content) > len(content)}


@router.post("/python")
async def execute_python(
    payload: PythonExecutionInput,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("tools:execute")),
) -> dict[str, object]:
    try:
        result = execute_restricted_python(payload.source)
    except RestrictedPythonViolation as exc:
        await record_audit(session, user.id, "tool.python.rejected", "python", "restricted", {"reason": str(exc)})
        await session.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await record_audit(
        session,
        user.id,
        "tool.python.executed",
        "python",
        "restricted",
        {"exit_code": result.exit_code},
    )
    await session.commit()
    return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code}
