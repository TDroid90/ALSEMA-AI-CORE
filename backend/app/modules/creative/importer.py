# The import runs in a dedicated ARQ worker and intentionally performs bounded,
# sequential filesystem copies so progress and rollback remain deterministic.
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.creative.models import (
    CreativeAsset,
    CreativeBrand,
    CreativeCatalogItem,
    CreativeJob,
    CreativeTemplate,
)
from app.modules.creative.schemas import CreativeContent
from app.modules.creative.storage import CreativeStorage

BRANDS = ("cometag", "clustersave", "peak", "canastapp", "instanews")


def _copy_tree(source: Path, destination: Path) -> int:
    if not source.exists():
        return 0
    count = 0
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        if not item.is_file():
            continue
        target = destination / item.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or item.stat().st_mtime_ns > target.stat().st_mtime_ns:
            shutil.copy2(item, target)
        count += 1
    return count


async def import_creativosur(
    session: AsyncSession, source_root: Path, storage: CreativeStorage
) -> dict[str, Any]:
    source_root = source_root.resolve()
    required = source_root / "creative_engine" / "composer.py"
    if not required.exists():
        raise ValueError("La carpeta no contiene una instalación válida de CreativoSur")
    counts = {"brands": 0, "catalog_items": 0, "templates": 0, "files": 0, "legacy_jobs": 0}
    brand_records: dict[str, CreativeBrand] = {}
    for slug in BRANDS:
        path = source_root / "brands" / f"{slug}.json"
        if not path.exists():
            continue
        profile = json.loads(path.read_text(encoding="utf-8"))
        brand = await session.scalar(select(CreativeBrand).where(CreativeBrand.slug == slug))
        if brand is None:
            brand = CreativeBrand(slug=slug, name=str(profile.get("name") or slug))
            session.add(brand)
            await session.flush()
        brand.name = str(profile.get("name") or brand.name)
        brand.profile_json = json.dumps(profile, ensure_ascii=False)
        brand_records[slug] = brand
        counts["brands"] += 1
    for slug, brand in brand_records.items():
        catalog_path = source_root / "data" / "catalog" / f"{slug}-products.json"
        if not catalog_path.exists():
            continue
        rows = json.loads(catalog_path.read_text(encoding="utf-8"))
        existing = {
            item.source_key: item
            for item in (
                await session.scalars(
                    select(CreativeCatalogItem).where(CreativeCatalogItem.brand_id == brand.id)
                )
            ).all()
        }
        for row in rows:
            key = str(row.get("id") or row.get("sku") or "").strip()
            if not key:
                continue
            item = existing.get(key)
            if item is None:
                item = CreativeCatalogItem(
                    brand_id=brand.id, source_key=key, title=str(row.get("title") or "Sin título")
                )
                session.add(item)
                existing[key] = item
            item.title = str(row.get("title") or "Sin título")
            item.category = str(row.get("category") or "")
            item.subcategory = str(row.get("subcategory") or "")
            item.source = str(row.get("source") or "CreativoSur import")
            item.payload_json = json.dumps(row, ensure_ascii=False)
            counts["catalog_items"] += 1
    template_paths = [*sorted((source_root / "data" / "template-editor").glob("*.json"))]
    for path in template_paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        key = path.stem
        latest = await session.scalar(
            select(CreativeTemplate)
            .where(CreativeTemplate.key == key)
            .order_by(CreativeTemplate.version.desc())
        )
        serialized = json.dumps(document, ensure_ascii=False)
        if latest is None or latest.document_json != serialized:
            session.add(
                CreativeTemplate(
                    key=key,
                    name=str(document.get("name") or key),
                    document_json=serialized,
                    version=(latest.version + 1) if latest else 1,
                    status="published",
                )
            )
        counts["templates"] += 1
    counts["files"] += _copy_tree(
        source_root / "data" / "catalog-assets", storage.resolve("catalog-assets")
    )
    counts["files"] += _copy_tree(source_root / "assets", storage.resolve("brands"))
    counts["files"] += _copy_tree(source_root / "outputs", storage.resolve("legacy-outputs"))
    database = source_root / "data" / "creativosur.db"
    if database.exists():
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        try:
            rows = connection.execute("SELECT id, status, payload FROM jobs").fetchall()
            for source_id, source_status, payload_json in rows:
                try:
                    source_uuid = UUID(str(source_id))
                    outputs = json.loads(payload_json)
                    first = outputs[0]
                    manifest = first["manifest"]
                    source_content = manifest["content"]
                    brand = brand_records.get(str(source_content.get("brand") or ""))
                    if brand is None:
                        continue
                    content = CreativeContent(
                        id=str(source_content.get("id") or source_id),
                        sku=source_content.get("sku"),
                        brand=brand.slug,
                        content_type=str(source_content.get("contentType") or "producto"),
                        campaign=str(source_content.get("campaign") or "producto"),
                        category=str(source_content.get("category") or ""),
                        subcategory=str(source_content.get("subcategory") or ""),
                        title=str(source_content.get("title") or "Creativo importado"),
                        short_title=source_content.get("shortTitle"),
                        description=str(source_content.get("description") or ""),
                        specs=[str(item) for item in source_content.get("specs", [])],
                        image_url=source_content.get("imageUrl"),
                        local_asset_key=str(source_content.get("id") or "") or None,
                        destination_url=source_content.get("destinationUrl"),
                        cta=str(source_content.get("cta") or "Ver producto"),
                        source=str(source_content.get("source") or "CreativoSur legacy"),
                        metadata={"legacy_job_id": str(source_id)},
                    )
                    job = await session.get(CreativeJob, source_uuid)
                    if job is None:
                        catalog_item = await session.scalar(
                            select(CreativeCatalogItem).where(
                                CreativeCatalogItem.brand_id == brand.id,
                                CreativeCatalogItem.source_key == content.id,
                            )
                        )
                        job = CreativeJob(
                            id=source_uuid,
                            brand_id=brand.id,
                            catalog_item_id=catalog_item.id if catalog_item else None,
                            status=str(source_status),
                            campaign=content.campaign,
                            format=str(manifest.get("format") or "instagram_feed"),
                            template_keys_json=json.dumps(
                                [
                                    str(output["manifest"].get("variant") or "A")
                                    for output in outputs
                                ]
                            ),
                            content_json=content.model_dump_json(),
                            provider_plan_json=json.dumps(
                                {"source": "creativosur-legacy", "compositor": "pillow"}
                            ),
                            qa_json=json.dumps(
                                {
                                    str(output["manifest"].get("variant") or "A"): output[
                                        "manifest"
                                    ].get("qa", {})
                                    for output in outputs
                                },
                                ensure_ascii=False,
                            ),
                        )
                        session.add(job)
                        await session.flush()
                    for output in outputs:
                        output_manifest = output["manifest"]
                        relative_url = str(output.get("url") or "").lstrip("/")
                        if not relative_url.startswith("outputs/"):
                            continue
                        source_storage_path = (
                            f"legacy-outputs/{relative_url.removeprefix('outputs/')}"
                        )
                        source_asset_path = storage.resolve(source_storage_path)
                        if not source_asset_path.exists():
                            continue
                        storage_path = f"legacy-jobs/{source_id}/{Path(relative_url).name}"
                        asset_path = storage.resolve(storage_path)
                        if not asset_path.exists():
                            storage.write_bytes(storage_path, source_asset_path.read_bytes())
                        existing_asset = await session.scalar(
                            select(CreativeAsset).where(CreativeAsset.storage_path == storage_path)
                        )
                        if existing_asset is not None:
                            continue
                        resolution = output_manifest.get("qa", {}).get("resolution", [None, None])
                        session.add(
                            CreativeAsset(
                                job_id=job.id,
                                kind="legacy_final",
                                variant=str(output_manifest.get("variant") or "A"),
                                storage_path=storage_path,
                                media_type="image/png",
                                sha256=storage.digest(storage_path),
                                size_bytes=asset_path.stat().st_size,
                                width=resolution[0],
                                height=resolution[1],
                                metadata_json=json.dumps(
                                    {"legacy_manifest": output_manifest}, ensure_ascii=False
                                ),
                            )
                        )
                    counts["legacy_jobs"] += 1
                except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                    continue
        finally:
            connection.close()
    await session.commit()
    return counts
