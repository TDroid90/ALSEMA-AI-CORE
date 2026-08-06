# Local operations

## Start

1. Copy `.env.example` to `.env` and replace the `CHANGE_ME` values.
2. Start Docker Desktop and Ollama on the Windows host.
3. From the repository root run:

```powershell
docker compose up -d --build
```

Open `http://localhost:5173`. On the first run, create the administrator in the
setup screen. The API is available at `http://localhost:8000/docs`.

## Health and diagnosis

```powershell
Invoke-RestMethod http://localhost:8000/health/ready
docker compose ps
docker compose logs --tail 100 api worker
```

Readiness is healthy only when PostgreSQL, Redis and the worker heartbeat are
available. Ollama is intentionally external and can be diagnosed in the dashboard
or from the provider API after authentication.

## Models

Use the **Modelos** screen to synchronize the catalog. Model downloads are started
only through an explicit authorized request. Existing Windows-host Ollama models
remain external to Docker by design.

## Data durability

`postgres_data`, `redis_data` and `tools_data` are named Docker volumes. Database
backup and restore are documented in `BACKUP_AND_RESTORE.md`.

## Stop

```powershell
docker compose down
```

This does not remove named volumes. Do not add `-v` unless deliberately discarding
all persisted local state.
