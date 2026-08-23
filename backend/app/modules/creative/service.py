import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.creative.models import (
    CreativeAsset,
    CreativeBrand,
    CreativeCatalogItem,
    CreativeJob,
)
from app.modules.creative.schemas import CreativeContent
from app.modules.creative.storage import CreativeStorage


def safe_source_key(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value)[:180]


def content_from_catalog(item: CreativeCatalogItem, brand: CreativeBrand) -> CreativeContent:
    payload = json.loads(item.payload_json)
    return CreativeContent(
        id=str(payload.get("id") or item.source_key),
        sku=payload.get("sku"),
        brand=brand.slug,
        content_type=str(payload.get("contentType") or "producto"),
        campaign=str(payload.get("campaign") or "producto"),
        category=str(payload.get("category") or item.category),
        subcategory=str(payload.get("subcategory") or item.subcategory),
        title=str(payload.get("title") or item.title),
        short_title=payload.get("shortTitle"),
        description=str(payload.get("description") or ""),
        specs=[str(value) for value in payload.get("specs", [])],
        image_url=payload.get("imageUrl"),
        destination_url=payload.get("destinationUrl"),
        cta=str(payload.get("cta") or "Ver producto"),
        source=str(payload.get("source") or item.source),
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
    )


def find_cutout(
    storage: CreativeStorage, brand: str, source_key: str, image_index: int = 0
) -> Path:
    stem = f"{brand}-{safe_source_key(source_key)}.image{image_index}.source.cutout.png"
    direct = storage.resolve(f"catalog-assets/{stem}")
    if direct.exists():
        return direct
    candidates = sorted(
        storage.resolve("catalog-assets").glob(
            f"{brand}-{safe_source_key(source_key)}.image{image_index}*.cutout.png"
        )
    )
    if candidates:
        return candidates[0]
    raise ValueError("esta foto necesita recorte: no se importó un recorte transparente")


async def serialize_job(session: AsyncSession, job: CreativeJob) -> dict[str, Any]:
    assets = (
        await session.scalars(
            select(CreativeAsset)
            .where(CreativeAsset.job_id == job.id)
            .order_by(CreativeAsset.created_at)
        )
    ).all()
    return {
        "id": str(job.id),
        "task_id": str(job.task_id) if job.task_id else None,
        "brand_id": str(job.brand_id),
        "catalog_item_id": str(job.catalog_item_id) if job.catalog_item_id else None,
        "status": job.status,
        "campaign": job.campaign,
        "format": job.format,
        "templates": json.loads(job.template_keys_json),
        "content": json.loads(job.content_json),
        "provider_plan": json.loads(job.provider_plan_json),
        "qa": json.loads(job.qa_json),
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "decided_at": job.decided_at.isoformat() if job.decided_at else None,
        "assets": [
            {
                "id": str(asset.id),
                "kind": asset.kind,
                "variant": asset.variant,
                "media_type": asset.media_type,
                "sha256": asset.sha256,
                "size_bytes": asset.size_bytes,
                "width": asset.width,
                "height": asset.height,
                "metadata": json.loads(asset.metadata_json),
            }
            for asset in assets
        ],
    }
