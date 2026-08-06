import json
from datetime import UTC, datetime
from typing import Literal
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
from app.modules.plugins.facebook import (
    FacebookAPIError,
    FacebookPublisherPlugin,
    credentials_for_facebook_account,
)
from app.modules.plugins.facebook_models import FacebookAccount, FacebookPublication
from app.modules.plugins.social_text import normalize_social_text
from app.modules.tasks.models import Task
from app.shared.database import get_session
from app.shared.secrets import SecretCipher

router = APIRouter(prefix="/api/v1/plugins/facebook", tags=["plugins", "facebook"])


class FacebookAccountCreate(BaseModel):
    account_label: str = Field(min_length=2, max_length=120)
    app_id: str = Field(min_length=1, max_length=120)
    app_secret: SecretStr
    page_id: str = Field(pattern=r"^\d{5,64}$")
    page_access_token: SecretStr
    api_version: str = Field(default="v26.0", pattern=r"^v\d+\.\d+$")
    enabled: bool = True
    auto_publish: bool = False


class FacebookAccountUpdate(BaseModel):
    account_label: str | None = Field(default=None, min_length=2, max_length=120)
    app_id: str | None = Field(default=None, min_length=1, max_length=120)
    app_secret: SecretStr | None = None
    page_id: str | None = Field(default=None, pattern=r"^\d{5,64}$")
    page_access_token: SecretStr | None = None
    api_version: str | None = Field(default=None, pattern=r"^v\d+\.\d+$")
    enabled: bool | None = None
    auto_publish: bool | None = None


class AccountReference(BaseModel):
    account_id: UUID


class FacebookImageCreate(BaseModel):
    account_id: UUID
    image_url: AnyHttpUrl
    caption: str = Field(min_length=1, max_length=63206)
    placement: Literal["feed", "story"] = "feed"

    @field_validator("caption")
    @classmethod
    def normalize_caption(cls, value: str) -> str:
        return normalize_social_text(value)

    @field_validator("image_url")
    @classmethod
    def require_public_https(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme != "https":
            raise ValueError("La imagen debe usar una URL HTTPS pública accesible por Meta.")
        host = (value.host or "").lower()
        if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
            raise ValueError("La imagen debe usar una URL pública, no una dirección local.")
        return value


class PublishConfirmation(BaseModel):
    confirmed: bool


def serialize_account(account: FacebookAccount) -> dict[str, object]:
    return {
        "id": str(account.id),
        "account_label": account.account_label,
        "app_id": account.app_id,
        "page_id": account.page_id,
        "api_version": account.api_version,
        "enabled": account.enabled,
        "auto_publish": account.auto_publish,
        "app_secret_configured": bool(account.app_secret_encrypted),
        "page_access_token_configured": bool(account.page_access_token_encrypted),
        "last_connection_status": account.last_connection_status,
        "last_connection_profile": json.loads(account.last_connection_profile_json or "{}"),
        "last_connection_at": account.last_connection_at.isoformat() if account.last_connection_at else None,
    }


def serialize_publication(publication: FacebookPublication, account_label: str | None = None) -> dict[str, object]:
    return {
        "id": str(publication.id),
        "account_id": str(publication.account_id),
        "account_label": account_label,
        "requested_by_user_id": str(publication.requested_by_user_id),
        "placement": publication.placement,
        "caption": publication.caption,
        "image_url": publication.image_url,
        "status": publication.status,
        "photo_id": publication.photo_id,
        "post_id": publication.post_id,
        "response": json.loads(publication.sanitized_response_json or "{}"),
        "error": publication.error,
        "created_at": publication.created_at.isoformat(),
        "updated_at": publication.updated_at.isoformat(),
        "ready_at": publication.ready_at.isoformat() if publication.ready_at else None,
        "published_at": publication.published_at.isoformat() if publication.published_at else None,
    }


async def enabled_account(session: AsyncSession, account_id: UUID) -> FacebookAccount:
    account = await session.get(FacebookAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Página de Facebook no encontrada.")
    if not account.enabled:
        raise HTTPException(status_code=409, detail="La página de Facebook está desactivada.")
    return account


@router.get("/accounts")
async def list_facebook_accounts(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    accounts = (await session.scalars(select(FacebookAccount).order_by(FacebookAccount.account_label))).all()
    return {"items": [serialize_account(account) for account in accounts]}


@router.post("/accounts", status_code=status.HTTP_201_CREATED)
async def create_facebook_account(
    payload: FacebookAccountCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    if await session.scalar(select(FacebookAccount).where(FacebookAccount.account_label == payload.account_label)):
        raise HTTPException(status_code=409, detail="Ya existe una página con esa etiqueta.")
    cipher = SecretCipher()
    account = FacebookAccount(
        account_label=payload.account_label,
        app_id=payload.app_id,
        app_secret_encrypted=cipher.encrypt(payload.app_secret.get_secret_value()),
        page_id=payload.page_id,
        page_access_token_encrypted=cipher.encrypt(payload.page_access_token.get_secret_value()),
        api_version=payload.api_version,
        enabled=payload.enabled,
        auto_publish=payload.auto_publish,
        created_by_user_id=user.id,
    )
    session.add(account)
    await session.flush()
    await record_audit(session, user.id, "facebook.account.created", "facebook_account", str(account.id), {"account_label": account.account_label})
    await session.commit()
    await session.refresh(account)
    return serialize_account(account)


@router.patch("/accounts/{account_id}")
async def update_facebook_account(
    account_id: UUID,
    payload: FacebookAccountUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    account = await session.get(FacebookAccount, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Página de Facebook no encontrada.")
    changes = payload.model_dump(exclude_unset=True, exclude={"app_secret", "page_access_token"})
    for key, value in changes.items():
        setattr(account, key, value)
    cipher = SecretCipher()
    if payload.app_secret is not None:
        account.app_secret_encrypted = cipher.encrypt(payload.app_secret.get_secret_value())
    if payload.page_access_token is not None:
        account.page_access_token_encrypted = cipher.encrypt(payload.page_access_token.get_secret_value())
    await record_audit(session, user.id, "facebook.account.updated", "facebook_account", str(account.id), {"fields": sorted(changes)})
    await session.commit()
    await session.refresh(account)
    return serialize_account(account)


@router.post("/test-connection")
async def test_facebook_connection(
    payload: AccountReference,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    account = await enabled_account(session, payload.account_id)
    try:
        profile = await FacebookPublisherPlugin().test_connection(credentials_for_facebook_account(account))
    except FacebookAPIError as exc:
        account.last_connection_status = "failed"
        account.last_connection_at = datetime.now(UTC)
        await record_audit(session, user.id, "facebook.connection.failed", "facebook_account", str(account.id), {"status_code": exc.status_code, "error": str(exc)})
        await session.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    account.last_connection_status = "connected"
    account.last_connection_profile_json = json.dumps(profile, ensure_ascii=False)
    account.last_connection_at = datetime.now(UTC)
    await record_audit(session, user.id, "facebook.connection.succeeded", "facebook_account", str(account.id), {"page_id": profile["id"]})
    await session.commit()
    return profile


@router.post("/media/image", status_code=status.HTTP_202_ACCEPTED)
async def create_facebook_image(
    payload: FacebookImageCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, str]:
    account = await enabled_account(session, payload.account_id)
    publication = FacebookPublication(
        account_id=account.id,
        requested_by_user_id=user.id,
        placement=payload.placement,
        caption=payload.caption,
        image_url=str(payload.image_url),
        status="queued",
    )
    task = Task(
        type="facebook.media.prepare",
        owner_user_id=user.id,
        status="queued",
        progress_total=2,
        progress_message="Publicación en cola",
    )
    session.add_all([publication, task])
    await session.flush()
    task.result = str(publication.id)
    await record_audit(session, user.id, "facebook.media.queued", "facebook_publication", str(publication.id), {"account_id": str(account.id), "placement": payload.placement})
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("prepare_facebook_media", str(task.id), str(publication.id))
    await pool.aclose()
    return {"publication_id": str(publication.id), "task_id": str(task.id), "status": "queued"}


@router.get("/media")
async def list_facebook_media(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, object]:
    rows = (
        await session.execute(
            select(FacebookPublication, FacebookAccount.account_label)
            .join(FacebookAccount, FacebookAccount.id == FacebookPublication.account_id)
            .order_by(FacebookPublication.created_at.desc())
            .limit(100)
        )
    ).all()
    return {"items": [serialize_publication(publication, label) for publication, label in rows]}


@router.post("/media/{publication_id}/publish", status_code=status.HTTP_202_ACCEPTED)
async def publish_facebook_media(
    publication_id: UUID,
    payload: PublishConfirmation,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("plugins:manage")),
) -> dict[str, str]:
    if not payload.confirmed:
        raise HTTPException(status_code=422, detail="La publicación requiere confirmación humana explícita.")
    publication = await session.get(FacebookPublication, publication_id)
    if publication is None:
        raise HTTPException(status_code=404, detail="Publicación de Facebook no encontrada.")
    if publication.status != "ready":
        raise HTTPException(status_code=409, detail="El contenido todavía no está listo para publicar.")
    await enabled_account(session, publication.account_id)
    task = Task(
        type="facebook.media.publish",
        owner_user_id=user.id,
        status="queued",
        progress_message="Publicación confirmada y en cola",
        result=str(publication.id),
    )
    session.add(task)
    await record_audit(session, user.id, "facebook.publish.confirmed", "facebook_publication", str(publication.id), {"placement": publication.placement})
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("publish_facebook_media", str(task.id), str(publication.id))
    await pool.aclose()
    return {"task_id": str(task.id), "publication_id": str(publication.id), "status": "queued"}
