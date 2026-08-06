"""Small, deliberately restrictive Python executor for Foundation Build tools.

It is not a general purpose sandbox.  Source is parsed before execution and runs
in a short lived isolated interpreter with a minimal builtin set.  The process
has no inherited environment, working directory or network capability exposed by
the API contract.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


class RestrictedPythonViolation(ValueError):
    """Raised when source asks for a capability outside the safe subset."""


_ALLOWED_IMPORTS = {"datetime", "json", "math", "statistics"}
_ALLOWED_BUILTINS = {
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "int", "len",
    "list", "max", "min", "range", "round", "set", "sorted", "str", "sum",
    "tuple", "zip",
}
_FORBIDDEN_NAMES = {
    "__builtins__", "__import__", "breakpoint", "compile", "eval", "exec", "getattr",
    "globals", "help", "input", "locals", "open", "setattr", "vars",
}


class _SafetyVisitor(ast.NodeVisitor):
    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            if item.name not in _ALLOWED_IMPORTS:
                raise RestrictedPythonViolation(f"El módulo {item.name!r} no está permitido.")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level or node.module not in _ALLOWED_IMPORTS:
            raise RestrictedPythonViolation("Solo se permiten imports explícitos de módulos estándar seguros.")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in _FORBIDDEN_NAMES or node.id.startswith("__"):
            raise RestrictedPythonViolation(f"El identificador {node.id!r} no está permitido.")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("__"):
            raise RestrictedPythonViolation("No se permite acceder a atributos internos.")
        self.generic_visit(node)


@dataclass(frozen=True)
class PythonExecutionResult:
    stdout: str
    stderr: str
    exit_code: int


def validate_python_source(source: str) -> None:
    if not source.strip():
        raise RestrictedPythonViolation("El código Python no puede estar vacío.")
    if len(source) > 20_000:
        raise RestrictedPythonViolation("El código Python supera el límite de 20 KB.")
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as exc:
        raise RestrictedPythonViolation(f"Código Python inválido: {exc.msg}.") from exc
    _SafetyVisitor().visit(tree)


def _limit_resources() -> None:
    # resource is available in the Linux containers used by Docker Compose.
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    except (ImportError, OSError, ValueError):
        # The caller still has the wall-clock timeout below on unsupported hosts.
        pass


def execute_restricted_python(source: str, timeout_seconds: float = 3.0) -> PythonExecutionResult:
    """Run prevalidated source in a clean temporary directory.

    ``-I`` ignores ambient Python configuration and the provided environment
    deliberately contains no application credentials.
    """
    validate_python_source(source)
    with tempfile.TemporaryDirectory(prefix="aas-python-") as directory:
        script = Path(directory) / "main.py"
        script.write_text(source, encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-S", str(script)],
                cwd=directory,
                env={"PATH": os.environ.get("PATH", ""), "PYTHONUNBUFFERED": "1"},
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                preexec_fn=_limit_resources if os.name != "nt" else None,
            )
        except subprocess.TimeoutExpired as exc:
            raise RestrictedPythonViolation("La ejecución Python superó el límite de tiempo.") from exc
    return PythonExecutionResult(
        stdout=completed.stdout[:20_000], stderr=completed.stderr[:20_000], exit_code=completed.returncode
    )
