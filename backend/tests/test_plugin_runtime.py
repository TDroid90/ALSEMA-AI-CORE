import pytest

from app.config.settings import Settings
from app.modules.plugins.runtime import (
    PluginRuntimeViolation,
    decode_docker_logs,
    sandbox_container_spec,
    validate_python_source,
)


def test_plugin_source_rejects_nul_and_empty_code() -> None:
    with pytest.raises(PluginRuntimeViolation):
        validate_python_source("\x00")
    with pytest.raises(PluginRuntimeViolation):
        validate_python_source("   ")


def test_plugin_source_accepts_bounded_python() -> None:
    validate_python_source("print('sandbox-ok')")


def test_docker_log_demultiplexing() -> None:
    frame = b"\x01\x00\x00\x00\x00\x00\x00\x03out\x02\x00\x00\x00\x00\x00\x00\x03err"
    assert decode_docker_logs(frame) == ("out", "err")


def test_sandbox_container_spec_has_no_host_or_network_escape() -> None:
    settings = Settings(
        app_secret_key="test-secret",
        database_url="postgresql+asyncpg://user:password@localhost:5432/test",
        redis_url="redis://localhost:6379/0",
        ollama_base_url="http://localhost:11434",
    )
    spec = sandbox_container_spec(settings, "print('safe')")
    host = spec["HostConfig"]
    assert spec["User"] == "65532:65532"
    assert spec["Env"] == ["PYTHONDONTWRITEBYTECODE=1", "PYTHONUNBUFFERED=1"]
    assert host == {
        "ReadonlyRootfs": True,
        "NetworkMode": "none",
        "CapDrop": ["ALL"],
        "SecurityOpt": ["no-new-privileges:true"],
        "PidsLimit": 64,
        "Memory": 134_217_728,
        "NanoCpus": 500_000_000,
        "Tmpfs": {"/tmp": "rw,noexec,nosuid,size=16m"},
        "Binds": [],
        "Privileged": False,
        "AutoRemove": False,
    }
