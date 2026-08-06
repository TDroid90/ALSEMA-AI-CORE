# Contributing

Read `CODEX_MASTER_PROMPT.md` and the canonical document index before changing the
platform. Keep business-specific integrations outside the Core.

## Before submitting a change

1. Add or update migration files for persistent schema changes.
2. Keep API routes under `/api/v1` and enforce a permission at the application
   boundary.
3. Never commit `.env`, credentials, model files or customer data.
4. Run `docker compose config`, the backend checks and frontend typecheck/build.
5. Document runtime evidence in `docs/IMPLEMENTATION_STATUS.md` when a phase is
   materially advanced.

Use small logical commits once Git author identity is configured locally.
