from dataclasses import dataclass

import httpx

from app.config.settings import Settings


@dataclass(frozen=True)
class ProviderHealth:
    status: str
    model_count: int | None
    detail: str | None


class OllamaHealthService:
    """Small adapter boundary; domain callers never consume Ollama's raw API."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = str(settings.ollama_base_url).rstrip("/")

    async def check(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                response.raise_for_status()
            payload = response.json()
            models = payload.get("models", [])
            return ProviderHealth("healthy", len(models) if isinstance(models, list) else None, None)
        except httpx.HTTPError:
            return ProviderHealth("unavailable", None, "Ollama no está disponible en la URL configurada.")

    async def list_models(self) -> list[dict[str, object]]:
        """Return a provider-neutral subset of the local Ollama catalog."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            raise RuntimeError("provider_unavailable") from error
        models = payload.get("models", [])
        if not isinstance(models, list):
            return []
        return [
            {
                "external_id": item.get("model"),
                "display_name": item.get("name"),
                "size_bytes": item.get("size"),
                "context_window": item.get("details", {}).get("context_length"),
                "capabilities": item.get("capabilities", []),
            }
            for item in models
            if isinstance(item, dict)
        ]
