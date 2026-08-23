from pathlib import Path

import pytest

from app.modules.creative.storage import CreativeStorage


def test_storage_rejects_path_traversal(tmp_path: Path) -> None:
    storage = CreativeStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.resolve("../escape.txt")


def test_storage_writes_atomically_and_hashes(tmp_path: Path) -> None:
    storage = CreativeStorage(tmp_path)
    path, digest = storage.write_bytes("jobs/test/output.txt", b"creative")
    assert path.read_bytes() == b"creative"
    assert digest == storage.digest("jobs/test/output.txt")
    assert not list(tmp_path.rglob("*.tmp"))
