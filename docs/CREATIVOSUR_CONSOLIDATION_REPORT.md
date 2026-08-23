# CreativoSur consolidation report

## Status

In progress on `feat/creativosur-consolidation`. This document is updated with verified evidence as each migration unit closes.

## Frozen baselines

- ALSEMA AI CORE: `f73799f45d324a6f512a5038f9bf18ecaf57c42b`
- CreativoSur: `a5632926a7f613c80b1a92a5ec7c737ec1f8d876`
- Source worktree at inspection: clean
- Target worktree at inspection: clean
- Docker Engine: 29.2.1
- GPU: NVIDIA GeForce RTX 3060, 12,288 MiB; 6,173 MiB free at inspection
- Installed Ollama models: `llama3.2:3b`, `qwen3:8b`, `qwen2.5-coder:14b`, `nomic-embed-text:latest`

## Initial service evidence

- PostgreSQL and Redis healthy.
- API, worker and frontend running in the ALSEMA Compose project.
- `GET /health/live`: `200 {"status":"ok"}`.
- `GET /health/ready`: `200`, PostgreSQL, Redis and worker true.
- Frontend `http://localhost:5173`: HTTP 200.
- Source CreativoSur inventory: 70 tracked files, SQLite database 184,320 bytes, 1.64 MB Cometa G catalog snapshot, 972 catalog asset files, 177 output files.

## Decisions

1. CreativoSur becomes a bounded native module, not a second service or a thin iframe.
2. Shared concerns use existing ALSEMA identity, API keys, permissions, tasks, provider interfaces, audit and configuration.
3. The specialist compositor/editor is migrated with behavioral tests before refactoring.
4. Existing business data is imported explicitly and idempotently; it is not committed as a hidden runtime dependency.
5. Social publishing remains outside the creative module and is never triggered automatically by creative generation.

## Verification log

Pending implementation. Commands, pass counts, migration counts, UI evidence and the three requested real creative IDs will be recorded here.

