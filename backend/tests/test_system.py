import json
import logging

from fastapi.testclient import TestClient

from app.main import JsonLogFormatter, app
from app.workers.arq import recoverable_task_job


def test_liveness_returns_ok() -> None:
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"].startswith("req_")


def test_recoverable_task_mapping_is_explicit() -> None:
    assert recoverable_task_job("system.smoke") == "run_smoke_task"
    assert recoverable_task_job("system.sleep") == "run_sleep_task"
    assert recoverable_task_job("provider.ollama.pull") is None


def test_json_log_formatter_emits_structured_event() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord("test", logging.INFO, "", 0, "completed %s", ("ok",), None)
    payload = json.loads(formatter.format(record))
    assert payload["logger"] == "test"
    assert payload["message"] == "completed ok"
    assert payload["level"] == "INFO"
