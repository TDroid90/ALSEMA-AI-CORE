import base64
import ipaddress
import json
import socket
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.modules.creative.models import CreativeTemplate
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.modules.instanews.renderer import render_social_asset
from app.modules.instanews.schemas import InstaNewsSocialAssetRequest
from app.modules.instanews.templates import OUTPUT_TEMPLATES, TEMPLATE_FAMILY, TEMPLATE_VERSION
from app.modules.plugins.facebook_models import FacebookAccount
from app.modules.plugins.instagram_models import InstagramAccount
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/instanews", tags=["instanews"])
ALLOWED_IMAGE_HOSTS = {"35.208.173.60", "instanews.news", "www.instanews.news", "drive.google.com", "lh3.googleusercontent.com"}


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
        png, text_fit = render_social_asset(image, payload.title, payload.summary, payload.category, definition)
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
