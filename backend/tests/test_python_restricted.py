import pytest

from app.modules.tools.python_restricted import RestrictedPythonViolation, execute_restricted_python


def test_restricted_python_runs_safe_standard_library_code() -> None:
    result = execute_restricted_python("import math\nprint(math.sqrt(81))")
    assert result.exit_code == 0
    assert result.stdout.strip() == "9.0"


@pytest.mark.parametrize("source", ["import os", "open('secret.txt')", "print((1).__class__)"])
def test_restricted_python_rejects_escape_capabilities(source: str) -> None:
    with pytest.raises(RestrictedPythonViolation):
        execute_restricted_python(source)
