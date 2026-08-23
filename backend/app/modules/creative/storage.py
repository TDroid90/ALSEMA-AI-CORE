from hashlib import sha256
from pathlib import Path


class CreativeStorageError(ValueError):
    pass


class CreativeStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise CreativeStorageError("La ruta intenta salir del almacenamiento creativo")
        return candidate

    def write_bytes(self, relative_path: str, content: bytes) -> tuple[Path, str]:
        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(content)
        temporary.replace(target)
        return target, sha256(content).hexdigest()

    def digest(self, relative_path: str) -> str:
        return sha256(self.resolve(relative_path).read_bytes()).hexdigest()
