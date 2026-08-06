from pathlib import Path

import pytest

from app.modules.tools.filesystem import SandboxFilesystem, SandboxViolation


def test_filesystem_tool_stays_inside_sandbox(tmp_path: Path) -> None:
    filesystem = SandboxFilesystem(tmp_path / "sandbox")
    filesystem.write_text("nested/file.txt", "verified")

    assert filesystem.read_text("nested/file.txt") == "verified"
    with pytest.raises(SandboxViolation):
        filesystem.resolve("../outside.txt")
