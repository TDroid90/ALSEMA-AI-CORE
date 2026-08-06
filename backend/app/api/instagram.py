import json
from datetime import UTC, datetime
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.config.settings import get_settings
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.modules.plugins.instagram import (
    InstagramAPIError,
    InstagramPublisherPlugin,
    credentials_for_account,
)
from app.modules.plugins.instagram_models import InstagramAccount, InstagramPublication
from app.modules.tasks.models import Task
from app.shared.database import get_session
from app.shared.secrets import SecretCipher

router = APIRouter(prefix="/api/v1/plugins/instagram", tags=["plugins", "instagram"])


class InstagramAccountCreate(BaseModel):
    account_label: str = Field(min_length=2, max_length=120)
    app_id: str = Field(min_length=1, max_length=120)
    app_secret: SecretStr
    instagram_user_id: str = Field(pattern=r"^\d{5,64}$")
    access_token: SecretStr
    api_version: str = Field(default="v23.0", pattern=r"^v\d+\.\d+$")
    enabled: bool = True


class InstagramAccountUpdate(BaseModel):
    account_label: str | None = Field(default=None, min_length=2, max_length=120)
    app_id: str | None = Field(default=None, min_length=1, max_length=120)
    app_secret: SecretStr | None = None
    instagram_user_id: str | None = Field(default=None, pattern=r"^\d{5,64}$")
    access_token: SecretStr | None = None
    api_version: str | None = Field(default=None, pattern=r"^v\d+\.\d+$")
    enabled: bool | None = None


class AccountReference(BaseModel):
    account_id: UUID


class InstagramImageCreate(BaseModel):
    account_id: UUID
    image_url: AnyHttpUrl
    caption: str = Field(min_length=1, max_length=2200)

    @field_validator("image_url")
    @classmethod
    def require_public_https(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme != "https":
            raise ValueError("La imagen debe usar una URL HTTPS pública accesible por Meta.")
        host = value.host or ""
        if host.lower() in {"localhost", "127.0.0.1", "::1"} or host.lower().endswith(".local"):
            raise ValueError("La imagen debe usar una URL pública, no una dirección local.")
        return value


class PublishConfirmation(BaseModel):
    confirmed: bool


def serialize_account(account: InstagramAccount) -> dict[str, object]:
    profile = json.loads(account.last_connection_profile_json or "{}")
    return {
        "id": str(account.id),
        "account_label": account.account_label,
        "app_id": account.app_id,
        "instagram_user_id": account.instagram_user_id,
        "api_version": account.api_version,
        "enabled": account.enabled,
        "app_secret_configured": bool(account.app_secret_encrypted),
        "access_token_configured": bool(account.access_token_encrypted),
        "last_connection_status": account.last_connection_status,
        "last_connection_profile": profile,
        "last_connection_at": account.last_connection_at.isoformat() if account.last_connection_at else None,
    }


def serialize_publication(publication: InstagramPublication, account_label: str | None = None) -> dict[str, object]:
    return {
        "id": str(publication.id),
        "account_id": str(publication.account_id),
        "account_label": account_label,
        "requested_by_user_id": str(publication.requested_by_user_id),
        "caption": publication.caption,
        "image_url": publication.image_url,
        "status": publication.status,
        "container_id": publication.container_id,
        "media_id": publication.media_id,
        "response": json.loads(publication.sanitized_response_json or "{}"),
        "error": publication.error,
        "created_at": publication.created_at.isoformat(),
        "updated_at": publication.updated_at.isoformat(),
        "ready_at": publication.ready_at.isoformat() if publication.ready_at else None,
        "published_at": publication.published_at.isoformat() if publication.published_at else None,
    }


async def enabled_account(session: AsyncSession, account_id: UUID) -> InstagramAccount:
    account = await session.get(InstagramAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Cuenta de Instagram no encontrada.")
    if not account.enabled:
        raise HTTPException(status_code=409, detail="La cuenta de Instagram está desactivada.")
    return account


@router.get("/accounts")
async def list_instagram_accounts(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    accounts = (await session.scalars(select(InstagramAccount).order_by(InstagramAccount.account_label))).all()
    return {"items": [serialize_account(account) for account in accounts]}


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
async def create_instagram_account(
    payload: InstagramAccountCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    if await session.scalar(select(InstagramAccount).where(InstagramAccount.account_label == payload.account_label)):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con esa etiqueta.")
    cipher = SecretCipher()
    account = InstagramAccount(
        account_label=payload.account_label,
        app_id=payload.app_id,
        app_secret_encrypted=cipher.encrypt(payload.app_secret.get_secret_value()),
        instagram_user_id=payload.instagram_user_id,
        access_token_encrypted=cipher.encrypt(payload.access_token.get_secret_value()),
        api_version=payload.api_version,
        enabled=payload.enabled,
        created_by_user_id=user.id,
    )
    session.add(account)
    await session.flush()
    await record_audit(session, user.id, "instagram.account.created", "instagram_account", str(account.id), {"account_label": account.account_label})
    await session.commit()
    await session.refresh(account)
    return serialize_account(account)


@router.patch("/accounts/{account_id}")
async def update_instagram_account(
    account_id: UUID,
    payload: InstagramAccountUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    account = await session.get(InstagramAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Cuenta de Instagram no encontrada.")
    changes = payload.model_dump(exclude_unset=True, exclude={"app_secret", "access_token"})
    for key, value in changes.items():
        setattr(account, key, value)
    cipher = SecretCipher()
    if payload.app_secret is not None:
        account.app_secret_encrypted = cipher.encrypt(payload.app_secret.get_secret_value())
    if payload.access_token is not None:
        account.access_token_encrypted = cipher.encrypt(payload.access_token.get_secret_value())
    await record_audit(session, user.id, "instagram.account.updated", "instagram_account", str(account.id), {"fields": sorted(changes)})
    await session.commit()
    await session.refresh(account)
    return serialize_account(account)


@router.post("/test-connection")
async def test_instagram_connection(
    payload: AccountReference,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    account = await enabled_account(session, payload.account_id)
    try:
        profile = await InstagramPublisherPlugin().test_connection(credentials_for_account(account))
    except InstagramAPIError as exc:
        account.last_connection_status = "failed"
        account.last_connection_at = datetime.now(UTC)
        await record_audit(session, user.id, "instagram.connection.failed", "instagram_account", str(account.id), {"status_code": exc.status_code, "error": str(exc)})
        await session.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    account.last_connection_status = "connected"
    account.last_connection_profile_json = json.dumps(profile, ensure_ascii=False)
    account.last_connection_at = datetime.now(UTC)
    await record_audit(session, user.id, "instagram.connection.succeeded", "instagram_account", str(account.id), {"profile_id": profile["id"]})
    await session.commit()
    return profile


@router.post("/media/image", status_code=status.HTTP_202_ACCEPTED)
async def create_instagram_image(
    payload: InstagramImageCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, str | None]:
    account = await enabled_account(session, payload.account_id)
    publication = InstagramPublication(
        account_id=account.id,
        requested_by_user_id=user.id,
        caption=payload.caption,
        image_url=str(payload.image_url),
        status="queued",
    )
    task = Task(
        type="instagram.media.prepare",
        owner_user_id=user.id,
        status="queued",
        progress_total=3,
        progress_message="Contenedor en cola",
    )
    session.add_all([publication, task])
    await session.flush()
    task.result = str(publication.id)
    await record_audit(session, user.id, "instagram.container.queued", "instagram_publication", str(publication.id), {"account_id": str(account.id)})
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("prepare_instagram_media", str(task.id), str(publication.id))
    await pool.aclose()
    return {"publication_id": str(publication.id), "task_id": str(task.id), "container_id": None, "status": "queued"}


@router.get("/media")
async def list_instagram_media(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    rows = (
        await session.execute(
            select(InstagramPublication, InstagramAccount.account_label)
            .join(InstagramAccount, InstagramAccount.id == InstagramPublication.account_id)
            .order_by(InstagramPublication.created_at.desc())
            .limit(100)
        )
    ).all()
    return {"items": [serialize_publication(publication, label) for publication, label in rows]}


@router.get("/media/{container_id}/status")
async def get_instagram_container_status(
    container_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    publication = await session.scalar(select(InstagramPublication).where(InstagramPublication.container_id == container_id))
    if publication is None:
        raise HTTPException(status_code=404, detail="Contenedor de Instagram no encontrado.")
    account = await enabled_account(session, publication.account_id)
    try:
        result = await InstagramPublisherPlugin().get_container_status(credentials_for_account(account), container_id)
    except InstagramAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"container_id": container_id, "status_code": result.get("status_code"), "status": result.get("status"), "publication_status": publication.status}


@router.post("/media/{container_id}/publish", status_code=status.HTTP_202_ACCEPTED)
async def publish_instagram_container(
    container_id: str,
    payload: PublishConfirmation,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, str]:
    if not payload.confirmed:
        raise HTTPException(status_code=422, detail="La publicación requiere confirmación humana explícita.")
    publication = await session.scalar(select(InstagramPublication).where(InstagramPublication.container_id == container_id))
    if publication is None:
        raise HTTPException(status_code=404, detail="Contenedor de Instagram no encontrado.")
    if publication.status != "ready":
        raise HTTPException(status_code=409, detail="El contenedor todavía no está listo para publicar.")
    await enabled_account(session, publication.account_id)
    task = Task(
        type="instagram.media.publish",
        owner_user_id=user.id,
        status="queued",
        progress_message="Publicación confirmada y en cola",
        result=str(publication.id),
    )
    session.add(task)
    await record_audit(session, user.id, "instagram.publish.confirmed", "instagram_publication", str(publication.id), {"container_id": container_id})
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("publish_instagram_media", str(task.id), str(publication.id))
    await pool.aclose()
    return {"task_id": str(task.id), "publication_id": str(publication.id), "status": "queued"}
