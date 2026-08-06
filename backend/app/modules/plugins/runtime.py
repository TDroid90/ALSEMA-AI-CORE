import time
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.config.settings import Settings


class PluginRuntimeViolation(ValueError):
    pass


@dataclass(frozen=True)
class PluginExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


class PluginExecutionRuntime(Protocol):
    async def execute_python(self, source: str) -> PluginExecutionResult: ...


def validate_python_source(source: str) -> None:
    if not source.strip() or len(source) > 20_000 or "\x00" in source:
        raise PluginRuntimeViolation("El código del plugin no es válido.")


def decode_docker_logs(payload: bytes) -> tuple[str, str]:
    stdout: list[bytes] = []
    stderr: list[bytes] = []
    offset = 0
    while offset + 8 <= len(payload):
        stream = payload[offset]
        size = int.from_bytes(payload[offset + 4:offset + 8], "big")
        chunk = payload[offset + 8:offset + 8 + size]
        if len(chunk) != size:
            break
        (stdout if stream == 1 else stderr).append(chunk)
        offset += 8 + size
    if offset != len(payload):
        stdout.append(payload[offset:])
    return (b"".join(stdout).decode("utf-8", errors="replace"), b"".join(stderr).decode("utf-8", errors="replace"))


def sandbox_container_spec(settings: Settings, source: str) -> dict[str, object]:
    """Build the entire Docker request server-side; plugin input controls only source."""
    validate_python_source(source)
    return {
        "Image": settings.plugin_sandbox_image,
        "User": "65532:65532",
        "Cmd": ["python", "-I", "-B", "-c", source],
        "Env": ["PYTHONDONTWRITEBYTECODE=1", "PYTHONUNBUFFERED=1"],
        "WorkingDir": "/tmp",
        "HostConfig": {
            "ReadonlyRootfs": True,
            "NetworkMode": "none",
            "CapDrop": ["ALL"],
            "SecurityOpt": ["no-new-privileges:true"],
            "PidsLimit": settings.plugin_sandbox_pids_limit,
            "Memory": settings.plugin_sandbox_memory_bytes,
            "NanoCpus": settings.plugin_sandbox_cpu_nano,
            "Tmpfs": {"/tmp": "rw,noexec,nosuid,size=16m"},
            "Binds": [],
            "Privileged": False,
            "AutoRemove": False,
        },
    }


class DockerSandboxRuntime:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def execute_python(self, source: str) -> PluginExecutionResult:
        started = time.monotonic()
        container_id = ""
        base_url = str(self.settings.plugin_docker_proxy_url).rstrip("/")
        payload = sandbox_container_spec(self.settings, source)
        try:
            async with httpx.AsyncClient(timeout=self.settings.plugin_sandbox_timeout_seconds + 5) as client:
                created = await client.post(f"{base_url}/containers/create", json=payload)
                created.raise_for_status()
                container_id = str(created.json()["Id"])
                started_response = await client.post(f"{base_url}/containers/{container_id}/start")
                started_response.raise_for_status()
                waited = await client.post(f"{base_url}/containers/{container_id}/wait", json={"condition": "not-running"}, timeout=self.settings.plugin_sandbox_timeout_seconds)
                waited.raise_for_status()
                exit_code = int(waited.json().get("StatusCode", 1))
                logs = await client.get(f"{base_url}/containers/{container_id}/logs", params={"stdout": "true", "stderr": "true", "timestamps": "false"})
                logs.raise_for_status()
        except httpx.TimeoutException as exc:
            raise PluginRuntimeViolation("El sandbox superó el tiempo máximo y fue cancelado.") from exc
        except (httpx.HTTPError, KeyError, TypeError) as exc:
            raise PluginRuntimeViolation("No se pudo ejecutar el sandbox de plugin.") from exc
        finally:
            if container_id:
                try:
                    async with httpx.AsyncClient(timeout=5) as cleanup:
                        await cleanup.delete(f"{base_url}/containers/{container_id}", params={"force": "true", "v": "true"})
                except httpx.HTTPError:
                    pass
        stdout, stderr = decode_docker_logs(logs.content)
        return PluginExecutionResult(stdout=stdout, stderr=stderr, exit_code=exit_code, duration_ms=int((time.monotonic() - started) * 1000))


class InProcessRuntime:
    async def execute_python(self, source: str) -> PluginExecutionResult:
        raise PluginRuntimeViolation("El runtime in_process no está habilitado para plugins externos.")


def execution_runtime(settings: Settings) -> PluginExecutionRuntime:
    return DockerSandboxRuntime(settings) if settings.plugin_runtime_mode == "docker_sandbox" else InProcessRuntime()
