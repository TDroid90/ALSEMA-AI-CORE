import json

import pytest
from fastapi import HTTPException

from app.api.agents import build_ollama_chat_body, validate_output_schema
from app.modules.agents.models import AgentVersion


def test_output_schema_accepts_valid_json_schema() -> None:
    validate_output_schema({"type": "object", "required": ["answer"], "properties": {"answer": {"type": "string"}}})


def test_output_schema_rejects_invalid_json_schema() -> None:
    with pytest.raises(HTTPException, match="JSON Schema"):
        validate_output_schema({"type": "not-a-json-schema-type"})


def test_structured_agent_passes_schema_to_ollama() -> None:
    schema = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "string"}},
    }
    version = AgentVersion(
        system_prompt="Return structured data.",
        model="qwen3:8b",
        temperature="0.2",
        output_schema_json=json.dumps(schema),
    )

    body = build_ollama_chat_body(version, "test input")

    assert body["format"] == schema
    assert body["think"] is False
    assert body["stream"] is False
