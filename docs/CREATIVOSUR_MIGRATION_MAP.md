# CreativoSur consolidation migration map

Date: 2026-08-23  
Target branch: `feat/creativosur-consolidation`  
ALSEMA baseline: `f73799f45d324a6f512a5038f9bf18ecaf57c42b`  
CreativoSur source baseline: `a5632926a7f613c80b1a92a5ec7c737ec1f8d876`

## Guardrails

- The source repository at `C:/Users/TD/Documents/Codex/2026-07-27/CreativoSur` is read-only during this migration.
- The only deployable product after consolidation is ALSEMA AI CORE. There is no iframe, second frontend, second API process, or second authentication system.
- Existing CreativoSur data is imported into PostgreSQL and ALSEMA-managed storage. Rollback consists of running the unchanged source repository again.
- Generated media always starts as `pending_approval`; no publisher is invoked by the creative module.
- Cometa G policy remains deterministic: real logo only, source facts only, no price/currency/installment/discount content.

## Source inventory

| Source capability | Current source | Target in ALSEMA | Migration treatment |
|---|---|---|---|
| Creative request schema and Cometa policy | `creative_engine/schemas.py` | `app/modules/creative/schemas.py`, policy service | Migrate and type strictly; keep policy tests |
| Pillow compositor and QA manifest | `creative_engine/composer.py` | `app/modules/creative/compositor.py` | Migrate implementation; replace source-root paths with storage ports |
| Catalog adapters | `catalogs/adapters.py` and JSON snapshots | creative catalog service and import command | Preserve read-only semantics; persist normalized records in PostgreSQL |
| Brand profiles | `brands/*.json` | `creative_brands` | Import, version, validate, expose under `/api/v1/creative/brands` |
| Templates A/B and professional editor documents | `templates/`, `data/template-editor` | `creative_templates` plus creative storage | Import JSON without changing layer semantics |
| Product source images and cutouts | `data/catalog-assets` | `/data/creative/assets` | Copy through explicit import; never reference host paths at runtime |
| Outputs and manifests | `outputs/` | `/data/creative/outputs` plus `creative_assets` | Import as historical assets; new outputs use immutable IDs |
| SQLite jobs | `data/creativosur.db` | `creative_jobs`, `creative_assets`, approval fields | One-shot idempotent data importer |
| Local text AI discovery | `local_ai/providers.py` | ALSEMA provider contracts | Ollama is primary; LM Studio remains an optional provider adapter/fallback |
| ComfyUI detection | `local_ai/providers.py` | creative visual provider port | Keep optional and degradable; no coupling to LLM providers |
| Publisher stubs | `publishers/adapters.py` | Existing ALSEMA social plugins | Do not migrate into creative execution; export/approval boundary only |
| Standalone FastAPI | `apps/api/main.py` | `app/api/creative.py` | Replace service key with ALSEMA JWT/API keys and `creative.*` permissions |
| Standalone React generator | `apps/web/src/main.tsx` | `/creativo` route in ALSEMA frontend | Migrate workflows and interaction patterns into ALSEMA shell |
| Professional template editor | `apps/web/src/editor.tsx` | `/creativo/templates/:id` | Migrate editor capabilities, not standalone navigation or API URLs |
| SQLite/background local jobs | inline source API | ALSEMA ARQ task handlers | Durable preparation/generation/import jobs with progress and retries |

## Target module boundaries

`app/modules/creative` owns creative brands, catalogs, templates, jobs, assets, QA, approval state, import, and provider-neutral visual orchestration. It may depend on public services from identity, tasks, providers, audit, and storage. Those shared modules must not depend on creative entities.

The HTTP surface is namespaced under `/api/v1/creative`. Static artifacts are served by authenticated or deliberately public asset endpoints using IDs, never arbitrary host paths.

Initial permissions:

- `creative.view`
- `creative.create`
- `creative.edit`
- `creative.generate`
- `creative.approve`
- `creative.export`
- `creative.manage_templates`
- `creative.manage_brands`
- `creative.manage_catalogs`
- `creative.manage_providers`

System administrators receive all permissions through the existing administrator bypass. Non-admin roles and API keys require explicit scopes.

## Persistence map

| Table | Purpose |
|---|---|
| `creative_brands` | Versioned brand profile and policy configuration |
| `creative_catalog_items` | Source facts and media references imported from catalog snapshots |
| `creative_templates` | Named, versioned template documents and renderer metadata |
| `creative_jobs` | Durable creative request, state, requested actor, provider plan, QA and approval |
| `creative_assets` | Source, cutout, preview, final and manifest artifacts with checksums |

No new credentials table is created. Provider and integration secrets remain in ALSEMA's existing secret/configuration boundary.

## Runtime and VRAM plan

- Ollama remains the primary local text provider through ALSEMA's provider service.
- ComfyUI is optional and used only through a `VisualGenerationProvider` port.
- Deterministic Pillow composition remains available when visual AI is down.
- The creative worker checks configured health before attempting AI enhancement and degrades to deterministic composition.
- The default concurrency for GPU-heavy creative work is one. A task must release the text-model workload before a visual stage; simultaneous large Ollama and ComfyUI workloads are not assumed safe on the detected RTX 3060 12 GB.
- LM Studio can be configured as an optional fallback provider later; it is not a second source of identity, jobs, or model catalog truth.

## Data migration procedure

1. Start the consolidated ALSEMA stack and apply Alembic migrations.
2. Invoke the administrative import command with the source repository path.
3. Hash and copy allowed JSON/media files into ALSEMA storage.
4. Upsert brands, catalog items and templates using stable source keys.
5. Import SQLite job rows as historical jobs, preserving source IDs in metadata.
6. Import existing output manifests/assets and compute checksums.
7. Produce counts and errors in an immutable audit event and import report.
8. Re-running the import must not duplicate records or overwrite newer ALSEMA edits.

## Rollback

The source repository is not edited, moved, or deleted. Before the first import, back up ALSEMA PostgreSQL and the creative storage volume. If consolidation must be rolled back, restore those ALSEMA resources and start CreativoSur from its documented scripts. No rollback step depends on reconstructed source code.

