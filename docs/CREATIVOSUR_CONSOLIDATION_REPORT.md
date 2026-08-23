# CreativoSur consolidation report

## BEFORE

CreativoSur was a standalone FastAPI/React application with its own localhost process, SQLite jobs, filesystem catalogs/assets, local provider discovery and separate navigation. ALSEMA AI CORE supplied none of its specialist creative surface.

Frozen baselines:

- ALSEMA AI CORE: `f73799f45d324a6f512a5038f9bf18ecaf57c42b`
- CreativoSur: `a5632926a7f613c80b1a92a5ec7c737ec1f8d876`
- Source inventory: 70 tracked files, 184,320-byte SQLite database, 972 catalog assets and 177 output files

## AFTER

CreativoSur is the native ALSEMA bounded module `/creativo` on `feat/creativosur-consolidation`. The final topology has one React frontend, FastAPI API, ALSEMA login/navigation/RBAC/audit, PostgreSQL, Redis/ARQ and one Docker Compose project. There is no iframe, second web server, second authentication system or creative-to-social auto-publish path.

## MIGRATED

- Brand profiles and Cometa G Product Lock policy: real product, source facts, real logo, no prices/currency/installments/discounts.
- CSV/JSON and read-only Google Sheets catalog adapters, indexed product images and `rembg` preparation.
- Pillow compositor, QA manifests, checksums, formats and A Product Hero/B Gaming/C Clean Tech directions.
- SQLite history, templates, catalog snapshots, cutouts, source media and legacy outputs.
- Professional layer editor: text/image/shape, positioning/scaling, undo/redo, z-order, locks, visibility, properties, JSON and PNG export.
- Native generator, production/history, catalogs, providers and explicit approval controls.

## REUSED

The proven specialist CreativoSur schemas, policy rules, Pillow composition behavior, catalog normalization, editor document model and editor interactions were ported into ALSEMA module boundaries. They were adapted for typed PostgreSQL entities, authenticated asset IDs and ALSEMA storage rather than reimplemented as placeholders.

## REPLACED

- Standalone login/service key → ALSEMA JWT/API-key and ten `creative.*` permissions.
- SQLite/in-process status → PostgreSQL plus durable ARQ tasks with progress, cancellation and audit.
- Source-root filesystem references → `/data/creative` named volume, normalized paths, atomic writes and SHA-256.
- Standalone React router/server → native ALSEMA shell route `/creativo` and production Nginx SPA fallback.
- Local provider probing → ALSEMA Ollama integration plus configurable visual/text fallback adapters.

## LEGACY

The original repository is retained only for rollback and remains unchanged/clean at `a5632926a7f613c80b1a92a5ec7c737ec1f8d876`. Imported historical jobs/assets keep source IDs in metadata. No ALSEMA runtime container mounts or launches the old application.

## AI

Ollama `qwen3:8b` is healthy and was used once per proof job to return strict structured product analysis, creative brief and factual copy. Installed local models also include `llama3.2:3b`, `qwen2.5-coder:14b` and `nomic-embed-text:latest`. LM Studio is an optional configurable fallback and is currently disabled because no URL was configured.

## VISUAL AI

- ComfyUI: adapter configured; currently unavailable, so generation degrades safely.
- FLUX: remains compatible behind the ComfyUI boundary; no active FLUX workflow was discovered or required by the source baseline.
- SSD: remains compatible behind the ComfyUI boundary; the original application only detected a local SSD checkpoint and did not use it in composition.
- rembg: installed in the worker and integrated as a durable indexed cutout task.
- Pillow: healthy deterministic production compositor used for the real proof run.

## DATABASE

Before import, PostgreSQL was exported to `/data/creative/backups/pre-creativosur-import-20260823.sql` with mode `0600`.

Import task `e1aa8521-212a-4e7f-9874-5da23526eef4` succeeded:

```json
{"brands":5,"catalog_items":1461,"templates":1,"files":1155,"legacy_jobs":56}
```

PostgreSQL normalized this to 5 brands, 1,434 unique catalog items, 1 template, 56 legacy jobs and 79 imported assets. Stable duplicate source keys explain the processed/unique catalog difference. After proof runs there are 58 jobs and 85 assets. Alembic reports `0022_creative_module (head)`.

## TESTING

- Ruff 0.11.13 changed surface: formatting and lint passed.
- Mypy 1.15.0 strict: no issues in 69 source files.
- Pytest 8.3.5: 56 passed, one dependency deprecation warning.
- Frontend TypeScript/typecheck and Vite production build: passed; 38 modules transformed.
- Production dependency audit: 0 vulnerabilities.
- Playwright Docker-hosted E2E: 1 passed for login/session, `/creativo`, ALSEMA navigation and design tokens.
- Health: `/health/live` 200; `/health/ready` has PostgreSQL, Redis and worker true.
- Docker: API, worker, frontend, PostgreSQL, Redis and restricted Docker proxy are up.

The E2E initially exposed undefined legacy CSS aliases (`--bg-panel`, `--accent`, `--accent-muted`). They now resolve to canonical ALSEMA tokens and the same E2E passed after the frontend image was rebuilt.

## FEATURE PARITY

The executable checklist in `docs/CREATIVOSUR_FEATURE_PARITY.md` is 100% verified for the source baseline and requested consolidation extension. Optional ComfyUI/FLUX/SSD paths are verified as configurable, safely unavailable boundaries because the source application also treated them as optional and did not execute them.

## REAL GENERATION

Cometa G product `elit-CH-351-MC`, job `fdf3280d-2a6b-4fa3-ad3e-caa2e0e5f279`, task `e7c452e9-ba37-4c22-a826-73c7311e4fcb`, status `pending_approval`:

- `/data/creative/outputs/fdf3280d-2a6b-4fa3-ad3e-caa2e0e5f279/A_instagram_feed.png` — 1080×1350, 1,220,751 bytes, `e1a774b3859b…`
- `/data/creative/outputs/fdf3280d-2a6b-4fa3-ad3e-caa2e0e5f279/B_instagram_feed.png` — 1080×1350, 1,127,625 bytes, `c2ea0c657de7…`
- `/data/creative/outputs/fdf3280d-2a6b-4fa3-ad3e-caa2e0e5f279/C_instagram_feed.png` — 1080×1350, 308,065 bytes, `7926f4c023b7…`

All three authenticated asset requests returned HTTP 200 `image/png`; QA is valid and approval remains pending. No approve, reject or publish action was executed. An earlier proof correctly failed because `.gitkeep` was considered a logo; discovery was restricted to approved image extensions before this successful run.

## BLOCKERS

No blocker prevents the consolidated Foundation workflow. ComfyUI is not running and LM Studio is not configured, but both are optional; Pillow plus Ollama are healthy and produced the acceptance artifacts.

## NEXT STEPS

1. Human-review the three proof assets in Creativo → Producción and approve or reject them explicitly.
2. Configure/start ComfyUI only when generative-background workflows are desired and validate the selected FLUX/SSD workflow on the 12 GB GPU.
3. Assign the minimum needed `creative.*` scopes to future service accounts instead of administrator access.
4. Add brand-specific catalogs through the native Catalogs screen without changing module code.
5. Schedule periodic PostgreSQL and `creative_data` volume backups before production use.

Start the sole product with `docker compose up -d --build`, then open `http://localhost:5173/creativo` through the normal ALSEMA login.
