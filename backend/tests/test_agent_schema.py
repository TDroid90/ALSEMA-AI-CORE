import pytest
from fastapi import HTTPException

from app.api.agents import validate_output_schema


def test_output_schema_accepts_valid_json_schema() -> None:
    validate_output_schema({"type": "object", "required": ["answer"], "properties": {"answer": {"type": "string"}}})


def test_output_schema_rejects_invalid_json_schema() -> None:
    with pytest.raises(HTTPException, match="JSON Schema"):
        validate_output_schema({"type": "not-a-json-schema-type"})
