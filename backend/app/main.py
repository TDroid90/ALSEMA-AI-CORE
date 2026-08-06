import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.api.access_admin import router as access_router
from app.api.agents import router as agents_router
from app.api.audit import router as audit_router
from app.api.conversations import router as conversations_router
from app.api.facebook import router as facebook_router
from app.api.identity import router as identity_router
from app.api.instagram import router as instagram_router
from app.api.memory import router as memory_router
from app.api.models import router as models_router
from app.api.plugins import router as plugins_router
from app.api.system import router as system_router
from app.api.tasks import router as tasks_router
from app.api.tools import router as tools_router
from app.api.workflows import router as workflows_router
from app.config.settings import get_settings
from app.modules.identity.bootstrap import bootstrap_initial_admin
from app.modules.plugins.instagram_bootstrap import bootstrap_instagram_account

logger = logging.getLogger("alsema.api")
logger.setLevel(logging.INFO)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            },
            ensure_ascii=False,
        )


if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
logger.propagate = False

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Request-ID"] = f"req_{uuid4()}"
        response.headers["X-Correlation-ID"] = request.headers.get("X-Correlation-ID", f"cor_{uuid4()}")
        logger.info("request_completed method=%s path=%s status=%s request_id=%s correlation_id=%s", request.method, request.url.path, response.status_code, response.headers["X-Request-ID"], response.headers["X-Correlation-ID"])
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in {"/health/live", "/health/ready"} or request.method == "OPTIONS":
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        key = f"aas:rate:{client}:{request.url.path}"
        redis = Redis.from_url(str(get_settings().redis_url))
        try:
            count = await redis.incr(key)
            if count == 1: await redis.expire(key, 60)
            if count > 120: return JSONResponse({"detail": "Rate limit excedido."}, status_code=429)
        finally:
            await redis.aclose()
        return await call_next(request)


class RequestSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > get_settings().max_request_body_bytes:
                    return JSONResponse({"detail": "Payload demasiado grande."}, status_code=413)
            except ValueError:
                return JSONResponse({"detail": "Content-Length inválido."}, status_code=400)
        return await call_next(request)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await bootstrap_initial_admin(get_settings())
    await bootstrap_instagram_account(get_settings())
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ALSEMA AI CORE", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestSizeMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-API-Key", "X-Correlation-ID"])
    app.include_router(system_router)
    app.include_router(identity_router)
    app.include_router(conversations_router)
    app.include_router(agents_router)
    app.include_router(tasks_router)
    app.include_router(memory_router)
    app.include_router(workflows_router)
    app.include_router(plugins_router)
    app.include_router(instagram_router)
    app.include_router(facebook_router)
    app.include_router(tools_router)
    app.include_router(models_router)
    app.include_router(access_router)
    app.include_router(audit_router)
    return app

app = create_app()
