# ADR 0007 — Consolidate CreativoSur as a native bounded module

- Status: Accepted
- Date: 2026-08-23

## Context

The original Foundation documentation treats business applications as external clients. A later product decision explicitly requires the existing CreativoSur application to be absorbed into ALSEMA AI CORE so users operate one SaaS, one login, one navigation and one runtime.

CreativoSur already contains valuable specialist behavior: deterministic image composition, brand rules, templates, a layer editor, cutout handling, QA manifests, catalogs and approval states. Replacing it with a new approximation would create parity risk.

## Decision

Create `creative` as a bounded module inside the ALSEMA modular monolith and expose it through the native `/creativo` frontend route and `/api/v1/creative` API namespace.

The module owns creative-domain entities and specialist rendering behavior. It consumes shared ALSEMA services for identity, authorization, API keys, tasks, providers, audit, configuration and storage. It does not introduce a separate server, frontend, database, login, worker or secrets system.

The source CreativoSur repository remains unchanged as the rollback baseline. Existing data is imported through an explicit, idempotent migration path.

## Consequences

- The Foundation rule that all business products are external now has one documented exception.
- Shared infrastructure stays generic; business-specific names and policies remain inside the creative boundary.
- Deployment and operation are simpler because only ALSEMA is started.
- The module must carry stronger architecture tests to prevent dependencies from leaking back into shared modules.
- Feature parity and rollback evidence are mandatory before retiring the standalone runtime.

## Rejected alternatives

- Iframe or reverse proxy to the old UI: violates the single-product requirement and preserves duplicate runtime concerns.
- Keep a second microservice: duplicates identity, jobs, configuration and deployment.
- Rewrite the creative engine: unnecessary regression risk and contrary to the migration directive.

