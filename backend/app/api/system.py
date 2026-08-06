import asyncio

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.dependencies import get_current_user
from app.config.settings import get_settings
from app.modules.identity.models import User
from app.modules.providers.application import OllamaHealthService

router = APIRouter(tags=["system"])

@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}

@router.get("/health/ready")
async def ready() -> JSONResponse:
    settings = get_settings()
    async def postgres() -> bool:
        engine = create_async_engine(str(settings.database_url))
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            await engine.dispose()
    async def redis() -> tuple[bool, bool]:
        client = Redis.from_url(settings.redis_url)
        try:
            redis_ok = bool(await client.ping())
            return redis_ok, bool(await client.get("aas:worker:heartbeat"))
        except Exception:
            return False, False
        finally:
            await client.aclose()
    db_ok, redis_result = await asyncio.gather(postgres(), redis())
    redis_ok, worker_ok = redis_result
    response = {"status": "ready" if db_ok and redis_ok and worker_ok else "not_ready", "components": {"postgres": db_ok, "redis": redis_ok, "worker": worker_ok}}
    return JSONResponse(response, status_code=status.HTTP_200_OK if db_ok and redis_ok and worker_ok else status.HTTP_503_SERVICE_UNAVAILABLE)

@router.get("/api/v1/system/status")
async def system_status() -> dict[str, object]:
    settings = get_settings()
    ollama = await OllamaHealthService(settings).check()
    return {"version": "0.1.0", "ollama": {"status": ollama.status, "model_count": ollama.model_count, "detail": ollama.detail}}


@router.get("/api/v1/providers/ollama/models")
async def list_ollama_models(user: User = Depends(get_current_user)) -> dict[str, object]:
    service = OllamaHealthService(get_settings())
    try:
        return {"items": await service.list_models()}
    except RuntimeError:
        return {"items": [], "error": {"code": "provider_unavailable", "message": "Ollama no está disponible."}}
