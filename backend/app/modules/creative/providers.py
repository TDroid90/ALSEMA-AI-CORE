from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass(frozen=True)
class VisualProviderHealth:
    status: str
    provider: str
    detail: str


class VisualGenerationProvider(Protocol):
    async def health(self) -> VisualProviderHealth: ...


class ComfyUIVisualProvider:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health(self) -> VisualProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/system_stats")
                response.raise_for_status()
            return VisualProviderHealth("healthy", "comfyui", "ComfyUI disponible")
        except httpx.HTTPError:
            return VisualProviderHealth(
                "unavailable",
                "comfyui",
                "ComfyUI no está disponible; se usará composición determinista.",
            )


class LMStudioTextFallback:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health(self) -> dict[str, object]:
        if not self.base_url:
            return {"status": "disabled", "model": None}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/v1/models")
                response.raise_for_status()
            models = response.json().get("data", [])
            return {
                "status": "healthy",
                "model": models[0].get("id") if models and isinstance(models[0], dict) else None,
            }
        except httpx.HTTPError:
            return {"status": "unavailable", "model": None}
