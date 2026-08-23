import csv
import io
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.creative.models import CreativeBrand, CreativeCatalogItem


def normalize_catalog_row(row: dict[str, Any], brand: str, source: str) -> dict[str, Any]:
    identifier = str(row.get("id") or row.get("sku") or "").strip()
    if not identifier:
        raise ValueError("Cada producto necesita id o sku")
    title = str(row.get("title") or row.get("nombre") or "").strip()
    if not title:
        raise ValueError(f"El producto {identifier} no tiene nombre")
    raw_specs = row.get("specs") or row.get("atributos") or []
    if isinstance(raw_specs, str):
        specs = [item.strip() for item in raw_specs.split("|") if item.strip()]
    elif isinstance(raw_specs, list):
        specs = [str(item).strip() for item in raw_specs if str(item).strip()]
    else:
        specs = []
    gallery = row.get("gallery") if isinstance(row.get("gallery"), list) else []
    image_url = row.get("imageUrl") or row.get("imagen_principal")
    return {
        "id": identifier,
        "sku": row.get("sku"),
        "brand": brand,
        "category": str(row.get("category") or row.get("categoria") or ""),
        "subcategory": str(row.get("subcategory") or row.get("subcategoria") or ""),
        "contentType": str(row.get("contentType") or "producto"),
        "campaign": "preventa"
        if str(row.get("preventa") or "").casefold() == "true"
        else str(row.get("campaign") or "producto"),
        "title": title,
        "shortTitle": str(row.get("shortTitle") or title),
        "description": str(row.get("description") or row.get("descripcion") or ""),
        "specs": specs[:5],
        "imageUrl": image_url,
        "gallery": gallery or ([image_url] if image_url else []),
        "destinationUrl": row.get("destinationUrl") or row.get("slug"),
        "cta": "Ver producto",
        "source": source,
        "metadata": row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
    }


def parse_catalog_file(raw: bytes, filename: str, brand: str) -> list[dict[str, Any]]:
    if len(raw) > 5_000_000:
        raise ValueError("El catálogo supera el límite de 5 MB")
    if filename.casefold().endswith(".json"):
        data = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(data, list):
            raise ValueError("El JSON debe contener una lista de productos")
        rows = data
    elif filename.casefold().endswith(".csv"):
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    else:
        raise ValueError("Usá un archivo JSON o CSV")
    return [normalize_catalog_row(row, brand, f"Archivo {filename}") for row in rows]


async def upsert_catalog(
    session: AsyncSession, brand_slug: str, rows: list[dict[str, Any]]
) -> dict[str, int]:
    brand = await session.scalar(select(CreativeBrand).where(CreativeBrand.slug == brand_slug))
    if brand is None:
        raise ValueError("La marca no existe")
    existing = {
        item.source_key: item
        for item in (
            await session.scalars(
                select(CreativeCatalogItem).where(CreativeCatalogItem.brand_id == brand.id)
            )
        ).all()
    }
    created = updated = 0
    for row in rows:
        key = str(row["id"])
        item = existing.get(key)
        if item is None:
            item = CreativeCatalogItem(brand_id=brand.id, source_key=key, title=str(row["title"]))
            session.add(item)
            created += 1
        else:
            updated += 1
        item.title = str(row["title"])
        item.category = str(row.get("category") or "")
        item.subcategory = str(row.get("subcategory") or "")
        item.source = str(row.get("source") or "catalog")
        item.payload_json = json.dumps(row, ensure_ascii=False)
        item.enabled = True
    await session.flush()
    return {"received": len(rows), "created": created, "updated": updated}
