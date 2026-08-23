import asyncio
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import UUID

import httpx
from arq.connections import ArqRedis
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.tools import validate_http_destination
from app.config.settings import get_settings
from app.modules.agents.models import Agent, AgentVersion
from app.modules.creative.compositor import manifest_bytes, render_creative
from app.modules.creative.importer import import_creativosur
from app.modules.creative.models import (
    CreativeAsset,
    CreativeBrand,
    CreativeCatalogItem,
    CreativeJob,
    CreativeTemplate,
)
from app.modules.creative.policy import validate_creative_policy
from app.modules.creative.providers import ComfyUIVisualProvider
from app.modules.creative.schemas import CreativeContent
from app.modules.creative.service import find_cutout
from app.modules.creative.storage import CreativeStorage
from app.modules.identity.audit import record_audit
from app.modules.plugins.facebook import (
    FacebookAPIError,
    FacebookPublisherPlugin,
    credentials_for_facebook_account,
)
from app.modules.plugins.facebook_models import FacebookAccount, FacebookPublication
from app.modules.plugins.instagram import (
    InstagramAPIError,
    InstagramPublisherPlugin,
    credentials_for_account,
)
from app.modules.plugins.instagram_models import InstagramAccount, InstagramPublication
from app.modules.tasks.models import Task
from app.modules.tools.filesystem import SandboxFilesystem, SandboxViolation
from app.modules.tools.python_restricted import RestrictedPythonViolation, execute_restricted_python
from app.modules.workflows.models import WorkflowRun, WorkflowVersion
from app.shared.database import SessionFactory
from app.shared.secrets import SecretDecryptionError


async def _enhance_creative_copy(
    content: CreativeContent,
) -> tuple[CreativeContent, dict[str, object]]:
    settings = get_settings()
    prompt = {
        "task": "Analizar el producto, crear un brief y mejorar el copy sin agregar hechos ni precios.",
        "rules": [
            "Usar solo los datos recibidos",
            "No incluir precio, moneda, cuotas, descuentos ni porcentajes",
            "Mantener el CTA exactamente igual",
            "El fondo y la dirección visual nunca deben inventar o reemplazar el producto real",
            "Reservar áreas seguras para producto, título, copy, CTA y logo",
            "Responder el contrato JSON completo",
        ],
        "content": content.model_dump(exclude={"metadata"}),
    }
    request = {
        "model": settings.creative_text_model,
        "messages": [
            {
                "role": "system",
                "content": "Sos un editor publicitario factual. Devolvé JSON estricto.",
            },
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "audience": {"type": "string"},
                        "selling_point": {"type": "string"},
                        "key_specs": {"type": "array", "items": {"type": "string"}},
                        "irrelevant_specs": {"type": "array", "items": {"type": "string"}},
                        "positioning": {"type": "string"},
                    },
                    "required": [
                        "category",
                        "audience",
                        "selling_point",
                        "key_specs",
                        "irrelevant_specs",
                        "positioning",
                    ],
                    "additionalProperties": False,
                },
                "brief": {
                    "type": "object",
                    "properties": {
                        "concept": {"type": "string"},
                        "hook": {"type": "string"},
                        "headline": {"type": "string"},
                        "cta": {"type": "string"},
                        "visual_direction": {"type": "string"},
                        "hierarchy": {"type": "string"},
                        "product_position": {"type": "string"},
                        "copy_position": {"type": "string"},
                        "lighting": {"type": "string"},
                        "background": {"type": "string"},
                        "negative_space": {"type": "string"},
                        "energy": {"type": "string"},
                        "safe_areas": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "concept",
                        "hook",
                        "headline",
                        "cta",
                        "visual_direction",
                        "hierarchy",
                        "product_position",
                        "copy_position",
                        "lighting",
                        "background",
                        "negative_space",
                        "energy",
                        "safe_areas",
                    ],
                    "additionalProperties": False,
                },
                "copy": {
                    "type": "object",
                    "properties": {
                        "short_title": {"type": "string"},
                        "description": {"type": "string"},
                        "specs": {
                            "type": "array",
                            "items": {"type": "string"},
                            "maxItems": 5,
                        },
                    },
                    "required": ["short_title", "description", "specs"],
                    "additionalProperties": False,
                },
            },
            "required": ["analysis", "brief", "copy"],
            "additionalProperties": False,
        },
        "options": {"temperature": 0.2},
    }
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{str(settings.ollama_base_url).rstrip('/')}/api/chat", json=request
            )
            response.raise_for_status()
        raw = response.json().get("message", {}).get("content", "")
        parsed = json.loads(raw)
        copy = parsed["copy"]
        candidate = content.model_copy(
            update={
                "short_title": str(copy["short_title"])[:500],
                "description": str(copy["description"])[:2000],
                "specs": [str(item) for item in copy["specs"]][:5],
            }
        )
        violations = validate_creative_policy(candidate)
        if violations:
            return content, {"status": "rejected", "provider": "ollama", "reason": violations}
        return candidate, {
            "status": "used",
            "provider": "ollama",
            "model": settings.creative_text_model,
            "product_analysis": parsed["analysis"],
            "creative_brief": parsed["brief"],
        }
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return content, {"status": "fallback", "provider": "ollama", "reason": type(exc).__name__}


async def import_creativosur_data(ctx: dict[str, object], task_id: str) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        if task is None or task.status != "queued":
            return
        task.status = "running"
        task.started_at = datetime.now(UTC)
        task.progress_message = "Validando el origen de CreativoSur"
        task.progress_current = 1
        await session.commit()
        try:
            storage = CreativeStorage(Path(get_settings().creative_storage_root))
            result = await import_creativosur(session, Path(task.result or ""), storage)
            task.status = "succeeded"
            task.progress_current = task.progress_total
            task.progress_message = "Importación de CreativoSur completada"
            task.result = json.dumps(result, ensure_ascii=False)
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                task.owner_user_id,
                "creative.import.completed",
                "creative_import",
                task_id,
                result,
            )
        except (OSError, ValueError, json.JSONDecodeError, sqlite3.Error, SQLAlchemyError) as exc:
            await session.rollback()
            task = await session.get(Task, UUID(task_id))
            if task is None:
                return
            task.status = "failed"
            task.error = str(exc)
            task.progress_message = "Falló la importación de CreativoSur"
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                task.owner_user_id,
                "creative.import.failed",
                "creative_import",
                task_id,
                {"error": str(exc)},
            )
        await session.commit()


async def prepare_creative_cutout(ctx: dict[str, object], task_id: str) -> None:
    del ctx
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        task_payload = json.loads(task.result) if task and task.result else {}
        item = (
            await session.get(CreativeCatalogItem, UUID(str(task_payload.get("item_id"))))
            if task_payload.get("item_id")
            else None
        )
        if task is None or item is None or task.status != "queued":
            return
        task.status = "running"
        task.started_at = datetime.now(UTC)
        task.progress_current = 1
        task.progress_message = "Localizando imagen original"
        await session.commit()
        try:
            brand = await session.get(CreativeBrand, item.brand_id)
            if brand is None:
                raise ValueError("La marca del catálogo ya no está disponible")
            storage = CreativeStorage(Path(get_settings().creative_storage_root))
            safe_key = re.sub(r"[^a-zA-Z0-9._-]+", "-", item.source_key)[:180]
            image_index = int(task_payload.get("image_index", 0))
            candidates = [
                path
                for path in sorted(
                    storage.resolve("catalog-assets").glob(
                        f"{brand.slug}-{safe_key}.image{image_index}.source.*"
                    )
                )
                if ".thumb." not in path.name and ".cutout." not in path.name
            ]
            if not candidates:
                raise ValueError("No se importó una imagen original para preparar el recorte")
            task.progress_current = 2
            task.progress_message = "Eliminando el fondo con rembg"
            await session.commit()
            from rembg import remove  # type: ignore[import-untyped]

            output = await asyncio.to_thread(remove, candidates[0].read_bytes())
            if not isinstance(output, bytes):
                raise ValueError("rembg no devolvió una imagen válida")
            destination = (
                f"catalog-assets/{brand.slug}-{safe_key}.image{image_index}.source.cutout.png"
            )
            _, digest = storage.write_bytes(destination, output)
            task.status = "succeeded"
            task.progress_current = task.progress_total
            task.progress_message = "Recorte transparente listo"
            task.result = json.dumps({"item_id": str(item.id), "image_index": image_index})
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                task.owner_user_id,
                "creative.cutout.completed",
                "creative_catalog_item",
                str(item.id),
                {"sha256": digest, "image_index": image_index},
            )
        except (OSError, ValueError) as exc:
            task.status = "failed"
            task.error = str(exc)
            task.progress_message = "Falló la preparación del recorte"
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                task.owner_user_id,
                "creative.cutout.failed",
                "creative_catalog_item",
                str(item.id),
                {"error": str(exc)},
            )
        await session.commit()


async def generate_creative(
    ctx: dict[str, object], task_id: str, creative_job_id: str | None = None
) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        resolved_job_id = creative_job_id or (task.result if task else None)
        job = await session.get(CreativeJob, UUID(resolved_job_id)) if resolved_job_id else None
        if task is None or job is None or task.status != "queued":
            return
        task.status = job.status = "running"
        task.started_at = job.started_at = datetime.now(UTC)
        task.progress_current = 1
        task.progress_message = "Preparando contenido y recursos"
        await session.commit()
        try:
            storage = CreativeStorage(Path(get_settings().creative_storage_root))
            brand = await session.get(CreativeBrand, job.brand_id)
            if brand is None:
                raise ValueError("La marca del creativo ya no está disponible")
            content = CreativeContent.model_validate_json(job.content_json)
            options = json.loads(job.options_json)
            provider_plan = json.loads(job.provider_plan_json)
            if options.get("use_text_ai"):
                content, text_result = await _enhance_creative_copy(content)
                provider_plan["text_result"] = text_result
                job.content_json = content.model_dump_json()
            if options.get("use_visual_ai"):
                visual_health = await ComfyUIVisualProvider(
                    get_settings().comfyui_base_url
                ).health()
                provider_plan["visual_result"] = {
                    "status": visual_health.status,
                    "detail": visual_health.detail,
                    "fallback": visual_health.status != "healthy",
                }
            catalog_item = (
                await session.get(CreativeCatalogItem, job.catalog_item_id)
                if job.catalog_item_id
                else None
            )
            source_key = catalog_item.source_key if catalog_item else content.local_asset_key
            if not source_key:
                raise ValueError("El contenido no tiene un recurso visual preparado")
            cutout = find_cutout(
                storage, brand.slug, source_key, int(options.get("image_index", 0))
            )
            logo_candidates = sorted(storage.resolve(f"brands/{brand.slug}/logo").glob("*"))
            logo = next(
                (
                    path
                    for path in logo_candidates
                    if path.is_file()
                    and path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}
                ),
                None,
            )
            templates = json.loads(job.template_keys_json)
            qa_by_variant: dict[str, object] = {}
            for index, template_key in enumerate(templates, start=1):
                await session.refresh(task)
                if task.status == "cancelling":
                    task.status = job.status = "cancelled"
                    task.progress_message = "Generación cancelada"
                    task.completed_at = job.completed_at = datetime.now(UTC)
                    await session.commit()
                    return
                task.progress_current = index + 1
                task.progress_message = f"Renderizando variante {template_key}"
                await session.commit()
                document = None
                variant = template_key
                if template_key.startswith("template:"):
                    key = template_key.split(":", 1)[1]
                    record = await session.scalar(
                        select(CreativeTemplate)
                        .where(CreativeTemplate.key == key, CreativeTemplate.status == "published")
                        .order_by(CreativeTemplate.version.desc())
                    )
                    if record is None:
                        raise ValueError(f"La plantilla {key} no está publicada")
                    document = json.loads(record.document_json)
                background = None
                if template_key in {"A", "B"}:
                    candidate = storage.resolve(
                        f"brands/{brand.slug}/backgrounds/Cooling ({1 if template_key == 'A' else 2}).png"
                    )
                    background = candidate if candidate.exists() else None
                rendered = render_creative(
                    content, variant, job.format, cutout, background, logo, document
                )
                base = f"outputs/{job.id}/{template_key.replace(':', '-')}_{job.format}"
                png_path, png_hash = storage.write_bytes(f"{base}.png", rendered.png)
                manifest = {
                    **rendered.manifest,
                    "job_id": str(job.id),
                    "provider_plan": provider_plan,
                }
                manifest_path, manifest_hash = storage.write_bytes(
                    f"{base}.manifest.json", manifest_bytes(manifest)
                )
                session.add_all(
                    [
                        CreativeAsset(
                            job_id=job.id,
                            kind="final",
                            variant=template_key,
                            storage_path=str(png_path.relative_to(storage.root)).replace("\\", "/"),
                            media_type="image/png",
                            sha256=png_hash,
                            size_bytes=len(rendered.png),
                            width=rendered.width,
                            height=rendered.height,
                            metadata_json=json.dumps(
                                {"manifest_hash": manifest_hash}, ensure_ascii=False
                            ),
                        ),
                        CreativeAsset(
                            job_id=job.id,
                            kind="manifest",
                            variant=template_key,
                            storage_path=str(manifest_path.relative_to(storage.root)).replace(
                                "\\", "/"
                            ),
                            media_type="application/json",
                            sha256=manifest_hash,
                            size_bytes=manifest_path.stat().st_size,
                            metadata_json=json.dumps(manifest, ensure_ascii=False),
                        ),
                    ]
                )
                qa_by_variant[template_key] = manifest["qa"]
                await session.commit()
            job.provider_plan_json = json.dumps(provider_plan, ensure_ascii=False)
            job.qa_json = json.dumps(qa_by_variant, ensure_ascii=False)
            invalid = [
                key
                for key, value in qa_by_variant.items()
                if not bool(cast(dict[str, object], value).get("valid"))
            ]
            if invalid:
                raise ValueError(f"Falló QA para las variantes: {', '.join(invalid)}")
            job.status = "pending_approval"
            job.completed_at = datetime.now(UTC)
            task.status = "succeeded"
            task.progress_current = task.progress_total
            task.progress_message = "Creativos listos; requieren aprobación humana"
            task.result = str(job.id)
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                job.owner_user_id,
                "creative.job.ready",
                "creative_job",
                str(job.id),
                {"templates": templates, "format": job.format},
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            job.status = task.status = "failed"
            job.error = task.error = str(exc)
            task.progress_message = "Falló la generación del creativo"
            task.completed_at = job.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                job.owner_user_id,
                "creative.job.failed",
                "creative_job",
                str(job.id),
                {"error": str(exc)},
            )
        await session.commit()


async def run_smoke_task(ctx: dict[str, object], task_id: str) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        if task is None:
            return
        task.status = "running"
        task.started_at = datetime.now(UTC)
        task.progress_message = "Procesando"
        await session.commit()
        task.progress_current = 1
        task.status = "succeeded"
        task.progress_message = "Completada"
        task.result = "smoke task completed"
        task.completed_at = datetime.now(UTC)
        await session.commit()


async def run_sleep_task(ctx: dict[str, object], task_id: str) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        if task is None or task.status != "queued":
            return
        seconds = int(task.result or "10")
        task.status = "running"
        task.started_at = datetime.now(UTC)
        task.progress_message = "Esperando cooperativamente"
        await session.commit()
        for current in range(1, seconds + 1):
            await asyncio.sleep(1)
            await session.refresh(task)
            if task.status == "cancelling":
                task.status = "cancelled"
                task.progress_message = "Cancelada cooperativamente"
                task.completed_at = datetime.now(UTC)
                await session.commit()
                return
            task.progress_current = current
            task.progress_message = f"Paso {current} de {seconds}"
            await session.commit()
        task.status = "succeeded"
        task.progress_message = "Completada"
        task.result = "sleep task completed"
        task.completed_at = datetime.now(UTC)
        await session.commit()


async def pull_ollama_model(ctx: dict[str, object], task_id: str) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        if task is None or task.status != "queued":
            return
        task.status = "running"
        task.started_at = datetime.now(UTC)
        task.progress_message = "Descargando modelo"
        await session.commit()
        try:
            async with httpx.AsyncClient(timeout=1800.0) as client:
                response = await client.post(
                    f"{str(get_settings().ollama_base_url).rstrip('/')}/api/pull",
                    json={"name": task.result, "stream": False},
                )
                response.raise_for_status()
            await session.refresh(task)
            if task.status == "cancelling":
                task.status = "cancelled"
                task.progress_message = "Cancelada cooperativamente"
            else:
                task.status = "succeeded"
                task.progress_current = 1
                task.progress_message = "Modelo descargado"
                task.result = json.dumps({"model": task.result})
        except httpx.HTTPError:
            task.attempt_count += 1
            if task.attempt_count < task.max_attempts:
                delay_seconds = min(2**task.attempt_count, 60)
                task.status = "queued"
                task.progress_message = (
                    f"Reintento {task.attempt_count + 1} programado en {delay_seconds}s"
                )
                await session.commit()
                redis = ctx.get("redis")
                if redis is not None:
                    await cast(ArqRedis, redis).enqueue_job(
                        "pull_ollama_model", task_id, _defer_by=delay_seconds
                    )
                return
            task.status = "failed"
            task.error = "No se pudo descargar el modelo desde el proveedor tras los reintentos."
        task.completed_at = datetime.now(UTC)
        await session.commit()


async def prepare_instagram_media(
    ctx: dict[str, object], task_id: str, publication_id: str | None = None
) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        if task is None or task.status not in {"queued", "uploading", "processing"}:
            return
        resolved_publication_id = publication_id or task.result
        if not resolved_publication_id:
            task.status = "failed"
            task.error = "La tarea no tiene una publicación asociada."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        publication = await session.get(InstagramPublication, UUID(resolved_publication_id))
        if publication is None:
            task.status = "failed"
            task.error = "La publicación asociada ya no existe."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        account = await session.get(InstagramAccount, publication.account_id)
        if account is None or not account.enabled:
            task.status = publication.status = "failed"
            task.error = publication.error = "La cuenta de Instagram no está disponible."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        plugin = InstagramPublisherPlugin(timeout=get_settings().http_timeout_seconds)
        try:
            credentials = credentials_for_account(account)
            if publication.container_id is None:
                task.status = publication.status = "uploading"
                task.started_at = task.started_at or datetime.now(UTC)
                task.progress_current = 1
                task.progress_message = "Creando contenedor de imagen"
                await session.commit()
                created = await plugin.create_image_container(
                    credentials,
                    publication.image_url,
                    publication.caption,
                    publication.placement,
                )
                container_id = created.get("id")
                if not isinstance(container_id, str) or not container_id:
                    raise InstagramAPIError(
                        "Instagram no devolvió el identificador del contenedor."
                    )
                publication.container_id = container_id
                publication.container_created_at = datetime.now(UTC)
                publication.sanitized_response_json = json.dumps(created, ensure_ascii=False)
            task.status = publication.status = "processing"
            task.progress_current = 2
            task.progress_message = "Instagram está procesando la imagen"
            await session.commit()
            deadline = (
                asyncio.get_running_loop().time()
                + get_settings().instagram_processing_timeout_seconds
            )
            while True:
                result = await plugin.get_container_status(credentials, publication.container_id)
                publication.sanitized_response_json = json.dumps(result, ensure_ascii=False)
                status_code = str(result.get("status_code", "")).upper()
                if status_code == "FINISHED":
                    task.status = publication.status = "ready"
                    task.progress_current = 3
                    task.progress_message = (
                        "Contenedor listo; publicación automática en cola"
                        if account.auto_publish
                        else "Contenedor listo; requiere confirmación humana"
                    )
                    task.completed_at = datetime.now(UTC)
                    publication.ready_at = datetime.now(UTC)
                    publication.error = None
                    await record_audit(
                        session,
                        publication.requested_by_user_id,
                        "instagram.container.ready",
                        "instagram_publication",
                        str(publication.id),
                        {"container_id": publication.container_id},
                    )
                    publish_task: Task | None = None
                    if account.auto_publish:
                        publish_task = Task(
                            type="instagram.media.publish",
                            owner_user_id=publication.requested_by_user_id,
                            status="queued",
                            progress_message="Publicación automática en cola",
                            result=str(publication.id),
                        )
                        session.add(publish_task)
                        await session.flush()
                        await record_audit(
                            session,
                            publication.requested_by_user_id,
                            "instagram.publish.automatic",
                            "instagram_publication",
                            str(publication.id),
                            {"container_id": publication.container_id},
                        )
                    await session.commit()
                    if publish_task is not None:
                        redis = ctx.get("redis")
                        if redis is not None:
                            await cast(ArqRedis, redis).enqueue_job(
                                "publish_instagram_media", str(publish_task.id), str(publication.id)
                            )
                    return
                if status_code in {"ERROR", "EXPIRED"}:
                    raise InstagramAPIError(
                        str(result.get("status", "Instagram no pudo procesar el contenedor."))
                    )
                if asyncio.get_running_loop().time() >= deadline:
                    raise InstagramAPIError(
                        "Instagram no terminó de procesar el contenedor dentro del tiempo permitido."
                    )
                await session.commit()
                await asyncio.sleep(get_settings().instagram_processing_poll_seconds)
        except (InstagramAPIError, SecretDecryptionError, ValueError) as exc:
            task.status = publication.status = "failed"
            task.error = publication.error = str(exc)
            task.progress_message = "Falló la preparación del contenedor"
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                publication.requested_by_user_id,
                "instagram.container.failed",
                "instagram_publication",
                str(publication.id),
                {"error": str(exc)},
            )
            await session.commit()


async def publish_instagram_media(
    ctx: dict[str, object], task_id: str, publication_id: str | None = None
) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        if task is None or task.status != "queued":
            return
        resolved_publication_id = publication_id or task.result
        publication = (
            await session.get(InstagramPublication, UUID(resolved_publication_id))
            if resolved_publication_id
            else None
        )
        if publication is None or publication.status != "ready" or not publication.container_id:
            task.status = "failed"
            task.error = "El contenedor no está listo para publicar."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        account = await session.get(InstagramAccount, publication.account_id)
        if account is None or not account.enabled:
            task.status = publication.status = "failed"
            task.error = publication.error = "La cuenta de Instagram no está disponible."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        task.status = publication.status = "publishing"
        task.started_at = datetime.now(UTC)
        task.progress_message = "Publicando el contenedor confirmado"
        await session.commit()
        try:
            result = await InstagramPublisherPlugin(
                timeout=get_settings().http_timeout_seconds
            ).publish_container(credentials_for_account(account), publication.container_id)
            media_id = result.get("id")
            if not isinstance(media_id, str) or not media_id:
                raise InstagramAPIError("Instagram no devolvió el identificador de la publicación.")
            publication.media_id = media_id
            publication.sanitized_response_json = json.dumps(result, ensure_ascii=False)
            publication.status = task.status = "published"
            publication.published_at = task.completed_at = datetime.now(UTC)
            publication.error = task.error = None
            task.progress_current = task.progress_total = 1
            task.progress_message = "Contenido publicado"
            await record_audit(
                session,
                publication.requested_by_user_id,
                "instagram.media.published",
                "instagram_publication",
                str(publication.id),
                {"container_id": publication.container_id, "media_id": media_id},
            )
        except (InstagramAPIError, SecretDecryptionError, ValueError) as exc:
            publication.status = task.status = "failed"
            publication.error = task.error = str(exc)
            task.progress_message = "Falló la publicación"
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                publication.requested_by_user_id,
                "instagram.publish.failed",
                "instagram_publication",
                str(publication.id),
                {"error": str(exc), "container_id": publication.container_id},
            )
        await session.commit()


async def prepare_facebook_media(
    ctx: dict[str, object], task_id: str, publication_id: str | None = None
) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        if task is None or task.status not in {"queued", "uploading"}:
            return
        resolved_publication_id = publication_id or task.result
        publication = (
            await session.get(FacebookPublication, UUID(resolved_publication_id))
            if resolved_publication_id
            else None
        )
        if publication is None:
            task.status = "failed"
            task.error = "La publicación asociada ya no existe."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        account = await session.get(FacebookAccount, publication.account_id)
        if account is None or not account.enabled:
            task.status = publication.status = "failed"
            task.error = publication.error = "La página de Facebook no está disponible."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        try:
            task.status = publication.status = "uploading"
            task.started_at = task.started_at or datetime.now(UTC)
            task.progress_current = 1
            task.progress_message = (
                "Subiendo foto no publicada para la historia"
                if publication.placement == "story"
                else "Validando publicación para el feed"
            )
            await session.commit()
            if publication.placement == "story" and publication.photo_id is None:
                result = await FacebookPublisherPlugin(
                    timeout=get_settings().http_timeout_seconds
                ).upload_story_photo(
                    credentials_for_facebook_account(account),
                    publication.image_url,
                    publication.caption,
                )
                photo_id = result.get("id")
                if not isinstance(photo_id, str) or not photo_id:
                    raise FacebookAPIError("Facebook no devolvió el identificador de la foto.")
                publication.photo_id = photo_id
                publication.sanitized_response_json = json.dumps(result, ensure_ascii=False)
            publication.status = task.status = "ready"
            publication.ready_at = task.completed_at = datetime.now(UTC)
            publication.error = task.error = None
            task.progress_current = task.progress_total = 2
            task.progress_message = (
                "Contenido listo; publicación automática en cola"
                if account.auto_publish
                else "Contenido listo; requiere confirmación humana"
            )
            await record_audit(
                session,
                publication.requested_by_user_id,
                "facebook.media.ready",
                "facebook_publication",
                str(publication.id),
                {"placement": publication.placement, "photo_id": publication.photo_id},
            )
            publish_task: Task | None = None
            if account.auto_publish:
                publish_task = Task(
                    type="facebook.media.publish",
                    owner_user_id=publication.requested_by_user_id,
                    status="queued",
                    progress_message="Publicación automática en cola",
                    result=str(publication.id),
                )
                session.add(publish_task)
                await session.flush()
                await record_audit(
                    session,
                    publication.requested_by_user_id,
                    "facebook.publish.automatic",
                    "facebook_publication",
                    str(publication.id),
                    {"placement": publication.placement},
                )
            await session.commit()
            if publish_task is not None:
                redis = ctx.get("redis")
                if redis is not None:
                    await cast(ArqRedis, redis).enqueue_job(
                        "publish_facebook_media", str(publish_task.id), str(publication.id)
                    )
        except (FacebookAPIError, SecretDecryptionError, ValueError) as exc:
            task.status = publication.status = "failed"
            task.error = publication.error = str(exc)
            task.progress_message = "Falló la preparación de Facebook"
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                publication.requested_by_user_id,
                "facebook.media.failed",
                "facebook_publication",
                str(publication.id),
                {"error": str(exc), "placement": publication.placement},
            )
            await session.commit()


async def publish_facebook_media(
    ctx: dict[str, object], task_id: str, publication_id: str | None = None
) -> None:
    async with SessionFactory() as session:
        task = await session.get(Task, UUID(task_id))
        if task is None or task.status != "queued":
            return
        resolved_publication_id = publication_id or task.result
        publication = (
            await session.get(FacebookPublication, UUID(resolved_publication_id))
            if resolved_publication_id
            else None
        )
        if publication is None or publication.status != "ready":
            task.status = "failed"
            task.error = "El contenido no está listo para publicar."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        account = await session.get(FacebookAccount, publication.account_id)
        if account is None or not account.enabled:
            task.status = publication.status = "failed"
            task.error = publication.error = "La página de Facebook no está disponible."
            task.completed_at = datetime.now(UTC)
            await session.commit()
            return
        task.status = publication.status = "publishing"
        task.started_at = datetime.now(UTC)
        task.progress_message = "Publicando en Facebook"
        await session.commit()
        try:
            plugin = FacebookPublisherPlugin(timeout=get_settings().http_timeout_seconds)
            credentials = credentials_for_facebook_account(account)
            if publication.placement == "story":
                if not publication.photo_id:
                    raise FacebookAPIError("La foto de la historia no fue preparada.")
                result = await plugin.publish_photo_story(credentials, publication.photo_id)
            else:
                result = await plugin.publish_feed_image(
                    credentials, publication.image_url, publication.caption
                )
                returned_photo_id = result.get("id")
                if isinstance(returned_photo_id, str):
                    publication.photo_id = returned_photo_id
            post_id = result.get("post_id") or result.get("id")
            if not isinstance(post_id, str) or not post_id:
                raise FacebookAPIError("Facebook no devolvió el identificador de la publicación.")
            publication.post_id = post_id
            publication.sanitized_response_json = json.dumps(result, ensure_ascii=False)
            publication.status = task.status = "published"
            publication.published_at = task.completed_at = datetime.now(UTC)
            publication.error = task.error = None
            task.progress_current = task.progress_total = 1
            task.progress_message = "Contenido publicado en Facebook"
            await record_audit(
                session,
                publication.requested_by_user_id,
                "facebook.media.published",
                "facebook_publication",
                str(publication.id),
                {"placement": publication.placement, "post_id": post_id},
            )
        except (FacebookAPIError, SecretDecryptionError, ValueError) as exc:
            publication.status = task.status = "failed"
            publication.error = task.error = str(exc)
            task.progress_message = "Falló la publicación en Facebook"
            task.completed_at = datetime.now(UTC)
            await record_audit(
                session,
                publication.requested_by_user_id,
                "facebook.publish.failed",
                "facebook_publication",
                str(publication.id),
                {"error": str(exc), "placement": publication.placement},
            )
        await session.commit()


async def run_workflow(ctx: dict[str, object], run_id: str) -> None:
    async with SessionFactory() as session:
        run = await session.get(WorkflowRun, UUID(run_id))
        if run is None or run.status != "queued":
            return
        run.status = "running"
        await session.commit()
        try:
            version = await session.get(WorkflowVersion, run.workflow_version_id)
            graph = json.loads(version.graph_json) if version else {}
            nodes = graph.get("nodes", [])
            node_ids = [node.get("id") for node in nodes]
            if not node_ids:
                raise ValueError("Workflow sin nodos")
            edges = graph.get("edges", [])
            children: dict[str, list[str]] = {str(node_id): [] for node_id in node_ids}
            incoming = {str(node_id): 0 for node_id in node_ids}
            for edge in edges:
                source, target = str(edge["from"]), str(edge["to"])
                children[source].append(target)
                incoming[target] += 1
            ready = [node_id for node_id, count in incoming.items() if count == 0]
            ordered_ids: list[str] = []
            while ready:
                node_id = ready.pop(0)
                ordered_ids.append(node_id)
                for target in children[node_id]:
                    incoming[target] -= 1
                    if incoming[target] == 0:
                        ready.append(target)
            if len(ordered_ids) != len(node_ids):
                raise ValueError("El workflow contiene un ciclo")

            node_by_id = {str(node["id"]): node for node in nodes}
            initial_input = json.loads(run.input_json)
            existing_state = json.loads(run.output_json) if run.output_json else {}
            outputs: dict[str, object] = existing_state.get("node_outputs", {})
            skipped: list[str] = existing_state.get("nodes_skipped", [])
            for node_id in ordered_ids:
                if node_id in outputs:
                    continue
                node = node_by_id[node_id]
                node_type = str(node.get("type", ""))
                incoming_edges = [edge for edge in edges if str(edge["to"]) == node_id]
                predecessors = [str(edge["from"]) for edge in incoming_edges]
                conditional_edges = [edge for edge in incoming_edges if "when" in edge]
                if conditional_edges and not any(
                    str(outputs.get(str(edge["from"]))).lower() == str(edge["when"]).lower()
                    for edge in conditional_edges
                ):
                    outputs[node_id] = None
                    skipped.append(node_id)
                    continue
                node_input: object = (
                    initial_input if not predecessors else outputs[predecessors[-1]]
                )
                if node_type == "condition":
                    field = node.get("field")
                    if not isinstance(field, str) or not isinstance(node_input, dict):
                        raise ValueError(
                            f"El nodo condition {node_id} requiere field y entrada de objeto"
                        )
                    outputs[node_id] = node_input.get(field) == node.get("equals", True)
                elif node_type == "approval":
                    decision = existing_state.get("approval", {})
                    if not isinstance(decision, dict):
                        decision = {}
                    if not decision:
                        run.output_json = json.dumps(
                            {
                                "input": initial_input,
                                "nodes_completed": list(outputs),
                                "nodes_skipped": skipped,
                                "node_outputs": outputs,
                                "approval_required": {
                                    "node_id": node_id,
                                    "reason": str(node.get("reason", "Aprobación requerida")),
                                },
                            },
                            ensure_ascii=False,
                        )
                        run.status = "waiting_approval"
                        await session.commit()
                        return
                    outputs[node_id] = decision.get("decision") == "approved"
                    if not outputs[node_id]:
                        raise ValueError(f"La aprobación del nodo {node_id} fue rechazada")
                elif node_type == "python":
                    source = node.get("source")
                    if not isinstance(source, str):
                        raise ValueError(f"El nodo python {node_id} requiere source")
                    try:
                        execution = execute_restricted_python(source)
                    except RestrictedPythonViolation as exc:
                        raise ValueError(f"El nodo python {node_id} fue rechazado: {exc}") from exc
                    if execution.exit_code != 0:
                        raise ValueError(
                            f"El nodo python {node_id} terminó con código {execution.exit_code}: {execution.stderr}"
                        )
                    outputs[node_id] = {"stdout": execution.stdout, "stderr": execution.stderr}
                elif node_type == "transform":
                    mapping = node.get("mapping", {})
                    if not isinstance(mapping, dict) or not isinstance(node_input, dict):
                        raise ValueError(
                            f"El nodo transform {node_id} requiere mapping y entrada de objeto"
                        )
                    outputs[node_id] = {
                        str(target): node_input.get(str(source))
                        for target, source in mapping.items()
                    }
                elif node_type == "file_read":
                    path = node.get("path")
                    if not isinstance(path, str):
                        raise ValueError(f"El nodo file_read {node_id} requiere path")
                    try:
                        outputs[node_id] = SandboxFilesystem(
                            Path(get_settings().tool_sandbox_root)
                        ).read_text(path)
                    except (FileNotFoundError, SandboxViolation) as exc:
                        raise ValueError(f"El nodo file_read {node_id} falló: {exc}") from exc
                elif node_type == "file_write":
                    path = node.get("path")
                    if not isinstance(path, str):
                        raise ValueError(f"El nodo file_write {node_id} requiere path")
                    content = node.get("content", node_input)
                    if not isinstance(content, str):
                        content = json.dumps(content, ensure_ascii=False)
                    try:
                        SandboxFilesystem(Path(get_settings().tool_sandbox_root)).write_text(
                            path, content
                        )
                    except SandboxViolation as exc:
                        raise ValueError(
                            f"El nodo file_write {node_id} fue rechazado: {exc}"
                        ) from exc
                    outputs[node_id] = {"path": path, "status": "written"}
                elif node_type == "http":
                    url = node.get("url")
                    if not isinstance(url, str):
                        raise ValueError(f"El nodo http {node_id} requiere url")
                    try:
                        safe_url = validate_http_destination(url)
                        async with httpx.AsyncClient(
                            timeout=get_settings().http_timeout_seconds,
                            follow_redirects=False,
                        ) as client:
                            response = await client.get(safe_url)
                    except (httpx.HTTPError, ValueError) as exc:
                        raise ValueError(f"El nodo http {node_id} falló: {exc}") from exc
                    content = response.content[: get_settings().http_max_response_bytes]
                    outputs[node_id] = {
                        "status_code": response.status_code,
                        "body": content.decode("utf-8", errors="replace"),
                        "truncated": len(response.content) > len(content),
                    }
                elif node_type == "delay":
                    seconds = node.get("seconds")
                    if (
                        not isinstance(seconds, int)
                        or isinstance(seconds, bool)
                        or not 0 <= seconds <= 300
                    ):
                        raise ValueError(f"El nodo delay {node_id} requiere seconds entre 0 y 300")
                    await asyncio.sleep(seconds)
                    outputs[node_id] = node_input
                elif node_type == "loop":
                    items_field = node.get("items_field")
                    max_iterations = node.get("max_iterations", 100)
                    if not isinstance(items_field, str) or not isinstance(node_input, dict):
                        raise ValueError(
                            f"El nodo loop {node_id} requiere items_field y entrada de objeto"
                        )
                    if (
                        not isinstance(max_iterations, int)
                        or isinstance(max_iterations, bool)
                        or not 1 <= max_iterations <= 1000
                    ):
                        raise ValueError(
                            f"El nodo loop {node_id} requiere max_iterations entre 1 y 1000"
                        )
                    items = node_input.get(items_field)
                    if not isinstance(items, list):
                        raise ValueError(
                            f"El nodo loop {node_id} requiere una lista en {items_field}"
                        )
                    if len(items) > max_iterations:
                        raise ValueError(f"El nodo loop {node_id} excede su máximo de iteraciones")
                    outputs[node_id] = [
                        {"index": index, "item": item} for index, item in enumerate(items)
                    ]
                elif node_type == "agent":
                    agent_id = node.get("agent_id")
                    if not isinstance(agent_id, str):
                        raise ValueError(f"El nodo agente {node_id} requiere agent_id")
                    agent = await session.get(Agent, UUID(agent_id))
                    if agent is None or agent.owner_user_id != run.owner_user_id:
                        raise ValueError(
                            f"El agente del nodo {node_id} no está disponible para este workflow"
                        )
                    agent_version = await session.scalar(
                        select(AgentVersion)
                        .where(
                            AgentVersion.agent_id == agent.id,
                            AgentVersion.status == "published",
                        )
                        .order_by(AgentVersion.version_number.desc())
                    )
                    if agent_version is None:
                        raise ValueError(f"El nodo agente {node_id} no tiene una versión publicada")
                    prompt = (
                        node_input
                        if isinstance(node_input, str)
                        else json.dumps(node_input, ensure_ascii=False)
                    )
                    body = {
                        "model": agent_version.model,
                        "messages": [
                            {"role": "system", "content": agent_version.system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": float(agent_version.temperature)},
                    }
                    try:
                        async with httpx.AsyncClient(timeout=300.0) as client:
                            response = await client.post(
                                f"{str(get_settings().ollama_base_url).rstrip('/')}/api/chat",
                                json=body,
                            )
                            response.raise_for_status()
                    except httpx.HTTPError as exc:
                        raise ValueError(f"Proveedor no disponible para el nodo {node_id}") from exc
                    outputs[node_id] = response.json().get("message", {}).get("content", "")
                else:
                    outputs[node_id] = node_input
            run.output_json = json.dumps(
                {
                    "input": initial_input,
                    "nodes_completed": ordered_ids,
                    "nodes_skipped": skipped,
                    "node_outputs": outputs,
                },
                ensure_ascii=False,
            )
            run.status = "succeeded"
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
        run.completed_at = datetime.now(UTC)
        await session.commit()
