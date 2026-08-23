import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import httpx
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission, require_system_admin
from app.config.settings import get_settings
from app.modules.creative.catalogs import normalize_catalog_row, parse_catalog_file, upsert_catalog
from app.modules.creative.models import (
    CreativeAsset,
    CreativeBrand,
    CreativeCatalogItem,
    CreativeJob,
    CreativeTemplate,
)
from app.modules.creative.policy import validate_creative_policy
from app.modules.creative.providers import ComfyUIVisualProvider, LMStudioTextFallback
from app.modules.creative.schemas import (
    CreateCreativeJob,
    CreativeDecision,
    CreativeImportRequest,
    CreativeTemplateInput,
    GoogleSheetsCatalogSync,
)
from app.modules.creative.service import content_from_catalog, find_cutout, serialize_job
from app.modules.creative.storage import CreativeStorage
from app.modules.identity.audit import record_audit
from app.modules.identity.models import User
from app.modules.providers.application import OllamaHealthService
from app.modules.tasks.models import Task
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/creative", tags=["creative"])


@router.get("/brands")
async def list_brands(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.view")),
) -> dict[str, object]:
    del user
    brands = (await session.scalars(select(CreativeBrand).order_by(CreativeBrand.name))).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "slug": item.slug,
                "name": item.name,
                "profile": json.loads(item.profile_json),
                "version": item.version,
                "enabled": item.enabled,
            }
            for item in brands
        ]
    }


@router.post("/catalog/import")
async def import_catalog_file(
    brand: str = Form(pattern=r"^[a-z0-9-]{2,80}$"),
    file: UploadFile = File(),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.manage_catalogs")),
) -> dict[str, int]:
    try:
        rows = parse_catalog_file(await file.read(5_000_001), file.filename or "catalog", brand)
        result = await upsert_catalog(session, brand, rows)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await record_audit(
        session,
        user.id,
        "creative.catalog.imported",
        "creative_catalog",
        brand,
        {**result, "filename": file.filename},
    )
    await session.commit()
    return result


@router.post("/catalog/google-sheets/sync")
async def sync_google_sheets_catalog(
    payload: GoogleSheetsCatalogSync,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.manage_catalogs")),
) -> dict[str, int]:
    url = (
        f"https://docs.google.com/spreadsheets/d/{payload.sheet_id}/export"
        f"?format=csv&gid={payload.gid}"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
        if len(response.content) > 5_000_000:
            raise ValueError("La exportación supera el límite de 5 MB")
        source_rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
        rows = [
            normalize_catalog_row(row, payload.brand, "Google Sheets (solo lectura)")
            for row in source_rows
        ]
        result = await upsert_catalog(session, payload.brand, rows)
    except (httpx.HTTPError, UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=422, detail=f"No se pudo sincronizar Google Sheets: {exc}"
        ) from exc
    await record_audit(
        session,
        user.id,
        "creative.catalog.google_sheets_synced",
        "creative_catalog",
        payload.brand,
        {**result, "sheet_id_suffix": payload.sheet_id[-6:], "gid": payload.gid},
    )
    await session.commit()
    return result


@router.get("/catalog")
async def list_catalog(
    brand: str,
    search: str = "",
    category: str = "",
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.view")),
) -> dict[str, object]:
    del user
    brand_record = await session.scalar(select(CreativeBrand).where(CreativeBrand.slug == brand))
    if brand_record is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada.")
    filters = [
        CreativeCatalogItem.brand_id == brand_record.id,
        CreativeCatalogItem.enabled.is_(True),
    ]
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                CreativeCatalogItem.title.ilike(pattern),
                CreativeCatalogItem.source_key.ilike(pattern),
            )
        )
    if category:
        filters.append(CreativeCatalogItem.category == category)
    statement = (
        select(CreativeCatalogItem)
        .where(*filters)
        .order_by(CreativeCatalogItem.title)
        .offset(offset)
        .limit(limit)
    )
    count = await session.scalar(
        select(func.count()).select_from(CreativeCatalogItem).where(*filters)
    )
    items = (await session.scalars(statement)).all()
    storage = CreativeStorage(Path(get_settings().creative_storage_root))

    def cutout_ready(source_key: str, image_index: int = 0) -> bool:
        try:
            find_cutout(storage, brand_record.slug, source_key, image_index)
        except ValueError:
            return False
        return True

    return {
        "items": [
            {
                "id": str(item.id),
                "source_key": item.source_key,
                "title": item.title,
                "category": item.category,
                "subcategory": item.subcategory,
                "source": item.source,
                "cutout_ready": cutout_ready(item.source_key),
                "prepared_images": [
                    image_index
                    for image_index in range(3)
                    if cutout_ready(item.source_key, image_index)
                ],
                "payload": json.loads(item.payload_json),
            }
            for item in items
        ],
        "total": count or 0,
        "offset": offset,
        "limit": limit,
    }


@router.post("/catalog/{item_id}/prepare", status_code=status.HTTP_202_ACCEPTED)
async def prepare_catalog_asset(
    item_id: UUID,
    image_index: int = Query(default=0, ge=0, le=2),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.edit")),
) -> dict[str, str]:
    item = await session.get(CreativeCatalogItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Elemento de catálogo no encontrado.")
    task = Task(
        type="creative.cutout",
        owner_user_id=user.id,
        result=json.dumps({"item_id": str(item.id), "image_index": image_index}),
        progress_total=3,
        progress_message="Preparación de imagen en cola",
    )
    session.add(task)
    await record_audit(
        session,
        user.id,
        "creative.cutout.queued",
        "creative_catalog_item",
        str(item.id),
        {"image_index": image_index},
    )
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("prepare_creative_cutout", str(task.id))
    await pool.aclose()
    return {"task_id": str(task.id), "status": task.status}


@router.get("/templates")
async def list_templates(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.view")),
) -> dict[str, object]:
    del user
    templates = (
        await session.scalars(select(CreativeTemplate).order_by(CreativeTemplate.created_at.desc()))
    ).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "key": item.key,
                "name": item.name,
                "description": item.description,
                "document": json.loads(item.document_json),
                "version": item.version,
                "status": item.status,
                "created_at": item.created_at.isoformat(),
            }
            for item in templates
        ]
    }


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def save_template(
    payload: CreativeTemplateInput,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.manage_templates")),
) -> dict[str, object]:
    latest = await session.scalar(
        select(CreativeTemplate)
        .where(CreativeTemplate.key == payload.key)
        .order_by(CreativeTemplate.version.desc())
    )
    template = CreativeTemplate(
        key=payload.key,
        name=payload.name,
        description=payload.description,
        document_json=json.dumps(payload.document, ensure_ascii=False),
        version=(latest.version + 1) if latest else 1,
        status="published" if payload.publish else "draft",
        created_by_user_id=user.id,
    )
    session.add(template)
    await record_audit(
        session,
        user.id,
        "creative.template.created",
        "creative_template",
        str(template.id),
        {"key": template.key, "version": template.version},
    )
    await session.commit()
    return {
        "id": str(template.id),
        "key": template.key,
        "version": template.version,
        "status": template.status,
    }


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.manage_templates")),
) -> None:
    template = await session.get(CreativeTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Versión de plantilla no encontrada.")
    await record_audit(
        session,
        user.id,
        "creative.template.deleted",
        "creative_template",
        str(template.id),
        {"key": template.key, "version": template.version},
    )
    await session.delete(template)
    await session.commit()


@router.get("/providers")
async def creative_provider_status(
    user: User = Depends(require_permission("creative.view")),
) -> dict[str, object]:
    del user
    settings = get_settings()
    ollama = await OllamaHealthService(settings).check()
    comfy = await ComfyUIVisualProvider(settings.comfyui_base_url).health()
    lm_studio = await LMStudioTextFallback(settings.lm_studio_base_url).health()
    return {
        "text": {
            "primary": {
                "provider": "ollama",
                "status": ollama.status,
                "model": settings.creative_text_model,
                "detail": ollama.detail,
            },
            "fallback": {"provider": "lm_studio", **lm_studio},
        },
        "visual": {"provider": comfy.provider, "status": comfy.status, "detail": comfy.detail},
        "deterministic_compositor": {"status": "healthy", "provider": "pillow"},
    }


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_creative_job(
    payload: CreateCreativeJob,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.generate")),
) -> dict[str, str]:
    brand = await session.scalar(
        select(CreativeBrand).where(
            CreativeBrand.slug == payload.brand, CreativeBrand.enabled.is_(True)
        )
    )
    if brand is None:
        raise HTTPException(status_code=404, detail="Marca no encontrada o deshabilitada.")
    catalog_item: CreativeCatalogItem | None = None
    if payload.catalog_item_id:
        catalog_item = await session.get(CreativeCatalogItem, payload.catalog_item_id)
        if catalog_item is None or catalog_item.brand_id != brand.id:
            raise HTTPException(status_code=404, detail="Elemento de catálogo no encontrado.")
        content = content_from_catalog(catalog_item, brand)
    elif payload.content:
        content = payload.content
    else:
        raise HTTPException(
            status_code=422, detail="Indicá un elemento de catálogo o contenido manual."
        )
    if content.brand != brand.slug:
        raise HTTPException(status_code=422, detail="La marca del contenido no coincide.")
    content.campaign = payload.campaign
    errors = validate_creative_policy(content)
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "El contenido viola la política de marca.", "errors": errors},
        )
    job = CreativeJob(
        owner_user_id=user.id,
        brand_id=brand.id,
        catalog_item_id=catalog_item.id if catalog_item else None,
        campaign=payload.campaign,
        format=payload.format,
        template_keys_json=json.dumps(payload.template_keys),
        content_json=content.model_dump_json(),
        options_json=json.dumps(
            {
                "use_text_ai": payload.use_text_ai,
                "use_visual_ai": payload.use_visual_ai,
                "image_index": payload.image_index,
            }
        ),
        provider_plan_json=json.dumps(
            {
                "text": "ollama" if payload.use_text_ai else "disabled",
                "visual": "comfyui" if payload.use_visual_ai else "deterministic",
                "compositor": "pillow",
            }
        ),
    )
    session.add(job)
    await session.flush()
    task = Task(
        type="creative.generate",
        owner_user_id=user.id,
        result=str(job.id),
        progress_total=len(payload.template_keys) + 2,
        progress_message="Creativo en cola",
    )
    session.add(task)
    await session.flush()
    job.task_id = task.id
    await record_audit(
        session,
        user.id,
        "creative.job.queued",
        "creative_job",
        str(job.id),
        {"brand": brand.slug, "templates": payload.template_keys, "format": payload.format},
    )
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("generate_creative", str(task.id), str(job.id))
    await pool.aclose()
    return {"job_id": str(job.id), "task_id": str(task.id), "status": job.status}


@router.get("/jobs")
async def list_creative_jobs(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.view")),
) -> dict[str, object]:
    statement = select(CreativeJob).order_by(CreativeJob.created_at.desc()).limit(100)
    if not user.is_system_admin:
        statement = statement.where(CreativeJob.owner_user_id == user.id)
    jobs = (await session.scalars(statement)).all()
    return {"items": [await serialize_job(session, job) for job in jobs]}


@router.get("/jobs/{job_id}")
async def get_creative_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.view")),
) -> dict[str, object]:
    job = await session.get(CreativeJob, job_id)
    if job is None or (not user.is_system_admin and job.owner_user_id != user.id):
        raise HTTPException(status_code=404, detail="Trabajo creativo no encontrado.")
    return await serialize_job(session, job)


@router.post("/jobs/{job_id}/decision")
async def decide_creative_job(
    job_id: UUID,
    payload: CreativeDecision,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.approve")),
) -> dict[str, str]:
    job = await session.get(CreativeJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Trabajo creativo no encontrado.")
    if job.status != "pending_approval":
        raise HTTPException(status_code=409, detail="El creativo no está pendiente de aprobación.")
    job.status = payload.decision
    job.approved_by_user_id = user.id
    job.approval_comment = payload.comment
    job.decided_at = datetime.now(UTC)
    await record_audit(
        session,
        user.id,
        f"creative.job.{payload.decision}",
        "creative_job",
        str(job.id),
        {"comment": payload.comment},
    )
    await session.commit()
    return {"id": str(job.id), "status": job.status}


@router.get("/assets/{asset_id}/content")
async def get_creative_asset(
    asset_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_permission("creative.view")),
) -> FileResponse:
    asset = await session.get(CreativeAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Archivo creativo no encontrado.")
    if asset.job_id:
        job = await session.get(CreativeJob, asset.job_id)
        if job is None or (not user.is_system_admin and job.owner_user_id != user.id):
            raise HTTPException(status_code=404, detail="Archivo creativo no encontrado.")
    storage = CreativeStorage(Path(get_settings().creative_storage_root))
    path = storage.resolve(asset.storage_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="El archivo ya no está disponible.")
    return FileResponse(path, media_type=asset.media_type, filename=path.name)


@router.post("/imports/creativosur", status_code=status.HTTP_202_ACCEPTED)
async def import_legacy_creativosur(
    payload: CreativeImportRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_system_admin),
) -> dict[str, str]:
    task = Task(
        type="creative.import",
        owner_user_id=user.id,
        result=payload.source_path,
        progress_total=5,
        progress_message="Importación en cola",
    )
    session.add(task)
    await record_audit(
        session,
        user.id,
        "creative.import.queued",
        "creative_import",
        None,
        {"source": payload.source_path},
    )
    await session.commit()
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("import_creativosur_data", str(task.id))
    await pool.aclose()
    return {"task_id": str(task.id), "status": task.status}
