import base64
import ipaddress
import json
import socket
from urllib.parse import urlparse

import httpx
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.config.settings import get_settings
from app.modules.creative.models import CreativeTemplate
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.modules.instanews.models import InstaNewsSocialDispatch
from app.modules.instanews.renderer import render_social_asset
from app.modules.instanews.schemas import (
    InstaNewsSocialAssetRequest,
    InstaNewsSocialPublishRequest,
)
from app.modules.instanews.templates import OUTPUT_TEMPLATES, TEMPLATE_FAMILY, TEMPLATE_VERSION
from app.modules.plugins.facebook_models import FacebookAccount, FacebookPublication
from app.modules.plugins.instagram_models import InstagramAccount, InstagramPublication
from app.modules.tasks.models import Task
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/instanews", tags=["instanews"])
ALLOWED_IMAGE_HOSTS = {"35.208.173.60", "instanews.news", "www.instanews.news", "drive.google.com", "lh3.googleusercontent.com"}
ACTIVE_PUBLICATION_STATUSES = {"queued", "uploading", "processing", "ready", "publishing"}
MAX_PUBLICATION_ATTEMPTS = 4


def _allowed_host(hostname: str) -> bool:
    host = hostname.casefold().strip(".")
    if host in ALLOWED_IMAGE_HOSTS or host.endswith(".public.blob.vercel-storage.com"):
        return True
    try:
        return not ipaddress.ip_address(host).is_private and host == "35.208.173.60"
    except ValueError:
        return False


async def _fetch_image(url: str) -> bytes:
    current = url
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        for _ in range(4):
            parsed = urlparse(current)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or not _allowed_host(parsed.hostname):
                raise HTTPException(status_code=422, detail="Origen de imagen no permitido.")
            try:
                addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))}
            except socket.gaierror as exc:
                raise HTTPException(status_code=422, detail="No se pudo resolver la imagen.") from exc
            if parsed.hostname != "35.208.173.60" and any(ipaddress.ip_address(address).is_private for address in addresses):
                raise HTTPException(status_code=422, detail="La imagen resuelve a una red privada.")
            response = await client.get(current, headers={"User-Agent": "ALSEMA-INSTANEWS/1.0"})
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location")
                if not location:
                    break
                current = str(response.url.join(location))
                continue
            if not response.is_success or not response.headers.get("content-type", "").casefold().startswith("image/"):
                raise HTTPException(status_code=422, detail="No se pudo descargar una imagen válida.")
            if len(response.content) > 20_000_000:
                raise HTTPException(status_code=413, detail="La imagen supera 20 MB.")
            return response.content
    raise HTTPException(status_code=422, detail="Demasiadas redirecciones de imagen.")


async def _latest_template(session: AsyncSession, output: str) -> tuple[CreativeTemplate, dict]:
    definition = OUTPUT_TEMPLATES[output]
    record = await session.scalar(
        select(CreativeTemplate)
        .where(CreativeTemplate.key == definition["key"], CreativeTemplate.status == "published")
        .order_by(CreativeTemplate.version.desc())
    )
    if record is None:
        raise HTTPException(status_code=503, detail=f"Falta la plantilla publicada {definition['name']}.")
    document = json.loads(record.document_json)
    return record, document.get("instanews") or definition


async def _instanews_account(session: AsyncSession, model: type[FacebookAccount] | type[InstagramAccount]):
    return await session.scalar(
        select(model)
        .where(
            model.account_label.ilike("%instanews%"),
            model.enabled.is_(True),
            model.auto_publish.is_(True),
        )
        .order_by(model.updated_at.desc())
    )


def _target_payload(publication: FacebookPublication | InstagramPublication | None) -> dict[str, object]:
    if publication is None:
        return {"status": "pending", "external_id": None, "permalink": None, "error": None, "published_at": None}
    external_id = publication.post_id if isinstance(publication, FacebookPublication) else publication.media_id
    permalink = None
    if isinstance(publication, FacebookPublication) and publication.post_id:
        parts = publication.post_id.split("_", 1)
        permalink = (
            f"https://www.facebook.com/{parts[0]}/posts/{parts[1]}"
            if len(parts) == 2
            else f"https://www.facebook.com/{publication.post_id}"
        )
    status = publication.status
    if status in ACTIVE_PUBLICATION_STATUSES:
        status = "processing"
    return {
        "status": status,
        "external_id": external_id,
        "permalink": permalink,
        "error": publication.error,
        "published_at": publication.published_at.isoformat() if publication.published_at else None,
    }


async def _serialize_dispatch(session: AsyncSession, dispatch: InstaNewsSocialDispatch) -> dict[str, object]:
    facebook = await session.get(FacebookPublication, dispatch.facebook_publication_id) if dispatch.facebook_publication_id else None
    instagram = await session.get(InstagramPublication, dispatch.instagram_publication_id) if dispatch.instagram_publication_id else None
    facebook_story = await session.get(FacebookPublication, dispatch.facebook_story_publication_id) if dispatch.facebook_story_publication_id else None
    instagram_story = await session.get(InstagramPublication, dispatch.instagram_story_publication_id) if dispatch.instagram_story_publication_id else None
    targets = [_target_payload(facebook), _target_payload(instagram), _target_payload(facebook_story), _target_payload(instagram_story)]
    statuses = [str(target["status"]) for target in targets]
    if all(status == "published" for status in statuses):
        dispatch.status, dispatch.error = "published", None
    elif "published" in statuses and "failed" in statuses:
        dispatch.status, dispatch.error = "partial", "Una plataforma no pudo publicar."
    elif "failed" in statuses:
        dispatch.status, dispatch.error = "failed", "No se pudo completar la publicación."
    elif any(status == "processing" for status in statuses):
        dispatch.status, dispatch.error = "processing", None
    await session.commit()
    return {
        "provider": "alsema",
        "news_id": dispatch.news_id,
        "status": dispatch.status,
        "attempts": dispatch.attempts,
        "error": dispatch.error,
        "facebook": targets[0],
        "instagram": targets[1],
        "facebook_story": targets[2],
        "instagram_story": targets[3],
        "created_at": dispatch.created_at.isoformat(),
        "updated_at": dispatch.updated_at.isoformat(),
    }


@router.get("/status")
async def instanews_status(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.view")),
) -> dict[str, object]:
    del user
    templates = []
    for output in OUTPUT_TEMPLATES:
        record, definition = await _latest_template(session, output)
        templates.append({"output": output, "id": str(record.id), "key": record.key, "name": record.name, "version": record.version, "status": record.status, "width": definition["width"], "height": definition["height"]})
    instagram = (await session.scalars(select(InstagramAccount).where(InstagramAccount.account_label.ilike("%instanews%")))).all()
    facebook = (await session.scalars(select(FacebookAccount).where(FacebookAccount.account_label.ilike("%instanews%")))).all()
    return {
        "template_family": TEMPLATE_FAMILY,
        "template_version": TEMPLATE_VERSION,
        "templates": templates,
        "instagram": [{"label": item.account_label, "enabled": item.enabled, "auto_publish": item.auto_publish, "connection": item.last_connection_status} for item in instagram],
        "facebook": [{"label": item.account_label, "enabled": item.enabled, "auto_publish": item.auto_publish, "connection": item.last_connection_status} for item in facebook],
    }


@router.post("/social-assets/generate")
async def generate_instanews_social_assets(
    payload: InstaNewsSocialAssetRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("agents:execute")),
) -> dict[str, object]:
    image = await _fetch_image(str(payload.image_url))
    rendered = []
    for output in dict.fromkeys(payload.outputs):
        record, definition = await _latest_template(session, output)
        png, text_fit = render_social_asset(image, payload.title, payload.summary, payload.category, definition, payload.city)
        rendered.append(
            {
                "output": output,
                "content_base64": base64.b64encode(png).decode("ascii"),
                "content_type": "image/png",
                "width": definition["width"],
                "height": definition["height"],
                "template_id": record.key,
                "template_version": str(record.version),
                "text_fit": text_fit,
            }
        )
    await record_audit(session, user.id, "instanews.social_assets.generated", "news", payload.news_id, {"outputs": list(dict.fromkeys(payload.outputs)), "template_family": TEMPLATE_FAMILY})
    await session.commit()
    return {"provider": "alsema", "template_family": TEMPLATE_FAMILY, "template_version": TEMPLATE_VERSION, "assets": rendered}


@router.get("/publishing-status")
async def instanews_publishing_status(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("agents:execute")),
) -> dict[str, object]:
    del user
    facebook = await _instanews_account(session, FacebookAccount)
    instagram = await _instanews_account(session, InstagramAccount)
    return {
        "provider": "alsema",
        "enabled": True,
        "configured": bool(facebook and instagram),
        "facebook_configured": facebook is not None,
        "instagram_configured": instagram is not None,
        "facebook_label": facebook.account_label if facebook else None,
        "instagram_label": instagram.account_label if instagram else None,
    }


@router.post("/social-publish", status_code=202)
async def publish_instanews_social(
    payload: InstaNewsSocialPublishRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("agents:execute")),
) -> dict[str, object]:
    facebook_account = await _instanews_account(session, FacebookAccount)
    instagram_account = await _instanews_account(session, InstagramAccount)
    if facebook_account is None or instagram_account is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "INSTANEWS_SOCIAL_ACCOUNTS_NOT_CONFIGURED",
                "facebook_configured": facebook_account is not None,
                "instagram_configured": instagram_account is not None,
            },
        )

    dispatch = await session.scalar(
        select(InstaNewsSocialDispatch).where(InstaNewsSocialDispatch.news_id == payload.news_id)
    )
    if dispatch is not None:
        current = await _serialize_dispatch(session, dispatch)
        if dispatch.status in {"published", "processing", "queued"} or dispatch.attempts >= MAX_PUBLICATION_ATTEMPTS:
            return current
        dispatch.title = payload.title
        dispatch.caption = payload.caption
        dispatch.feed_image_url = str(payload.feed_image_url)
        dispatch.story_image_url = str(payload.story_image_url)
        dispatch.attempts += 1
        dispatch.status = "queued"
        dispatch.error = None
    else:
        dispatch = InstaNewsSocialDispatch(
            news_id=payload.news_id,
            title=payload.title,
            caption=payload.caption,
            feed_image_url=str(payload.feed_image_url),
            story_image_url=str(payload.story_image_url),
            status="queued",
            attempts=1,
        )
        session.add(dispatch)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            existing = await session.scalar(
                select(InstaNewsSocialDispatch).where(InstaNewsSocialDispatch.news_id == payload.news_id)
            )
            if existing is None:
                raise
            return await _serialize_dispatch(session, existing)

    previous_facebook = await session.get(FacebookPublication, dispatch.facebook_publication_id) if dispatch.facebook_publication_id else None
    previous_instagram = await session.get(InstagramPublication, dispatch.instagram_publication_id) if dispatch.instagram_publication_id else None
    previous_facebook_story = await session.get(FacebookPublication, dispatch.facebook_story_publication_id) if dispatch.facebook_story_publication_id else None
    previous_instagram_story = await session.get(InstagramPublication, dispatch.instagram_story_publication_id) if dispatch.instagram_story_publication_id else None
    jobs: list[tuple[str, Task, FacebookPublication | InstagramPublication]] = []

    if previous_facebook is None or previous_facebook.status == "failed":
        publication = FacebookPublication(
            account_id=facebook_account.id,
            requested_by_user_id=user.id,
            placement="feed",
            caption=payload.caption,
            image_url=str(payload.feed_image_url),
            status="queued",
        )
        task = Task(type="facebook.media.prepare", owner_user_id=user.id, status="queued", progress_total=2, progress_message="Publicación INSTANEWS en cola")
        session.add_all([publication, task])
        await session.flush()
        task.result = str(publication.id)
        dispatch.facebook_publication_id = publication.id
        jobs.append(("prepare_facebook_media", task, publication))

    if previous_instagram is None or previous_instagram.status == "failed":
        publication = InstagramPublication(
            account_id=instagram_account.id,
            requested_by_user_id=user.id,
            placement="feed",
            caption=payload.caption,
            image_url=str(payload.feed_image_url),
            status="queued",
        )
        task = Task(type="instagram.media.prepare", owner_user_id=user.id, status="queued", progress_total=3, progress_message="Publicación INSTANEWS en cola")
        session.add_all([publication, task])
        await session.flush()
        task.result = str(publication.id)
        dispatch.instagram_publication_id = publication.id
        jobs.append(("prepare_instagram_media", task, publication))

    if previous_facebook_story is None or previous_facebook_story.status == "failed":
        publication = FacebookPublication(
            account_id=facebook_account.id,
            requested_by_user_id=user.id,
            placement="story",
            caption=payload.caption,
            image_url=str(payload.story_image_url),
            status="queued",
        )
        task = Task(type="facebook.media.prepare", owner_user_id=user.id, status="queued", progress_total=2, progress_message="Historia INSTANEWS en cola")
        session.add_all([publication, task])
        await session.flush()
        task.result = str(publication.id)
        dispatch.facebook_story_publication_id = publication.id
        jobs.append(("prepare_facebook_media", task, publication))

    if previous_instagram_story is None or previous_instagram_story.status == "failed":
        publication = InstagramPublication(
            account_id=instagram_account.id,
            requested_by_user_id=user.id,
            placement="story",
            caption=payload.caption,
            image_url=str(payload.story_image_url),
            status="queued",
        )
        task = Task(type="instagram.media.prepare", owner_user_id=user.id, status="queued", progress_total=3, progress_message="Historia INSTANEWS en cola")
        session.add_all([publication, task])
        await session.flush()
        task.result = str(publication.id)
        dispatch.instagram_story_publication_id = publication.id
        jobs.append(("prepare_instagram_media", task, publication))

    await record_audit(
        session,
        user.id,
        "instanews.social_publish.queued",
        "instanews_social_dispatch",
        str(dispatch.id),
        {"news_id": payload.news_id, "attempt": dispatch.attempts, "targets": ["facebook_feed", "facebook_story", "instagram_feed", "instagram_story"]},
    )
    await session.commit()

    try:
        pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
        try:
            for job_name, task, publication in jobs:
                await pool.enqueue_job(job_name, str(task.id), str(publication.id))
        finally:
            await pool.aclose()
    except Exception as exc:
        dispatch.status = "failed"
        dispatch.error = f"No se pudo encolar la publicación: {str(exc)[:180]}"
        for _, task, publication in jobs:
            task.status = publication.status = "failed"
            task.error = publication.error = dispatch.error
        await session.commit()
        raise HTTPException(status_code=503, detail="INSTANEWS_SOCIAL_QUEUE_UNAVAILABLE") from exc

    return await _serialize_dispatch(session, dispatch)


@router.get("/social-publish/{news_id}")
async def get_instanews_social_publish(
    news_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("agents:execute")),
) -> dict[str, object]:
    del user
    dispatch = await session.scalar(
        select(InstaNewsSocialDispatch).where(InstaNewsSocialDispatch.news_id == news_id)
    )
    if dispatch is None:
        raise HTTPException(status_code=404, detail="INSTANEWS_SOCIAL_DISPATCH_NOT_FOUND")
    return await _serialize_dispatch(session, dispatch)
