# Implementation status

## Instagram publisher

- Generic multi-account integration using `https://graph.instagram.com`.
- App secrets and access tokens are encrypted before persistence and never returned by API.
- Connection testing, image-container creation, status polling, durable ARQ state and publication history are available under `/api/v1/plugins/instagram`.
- Publishing is split from preparation and requires an authenticated human confirmation payload.
- Unit and simulated integration tests verify redaction, encryption and that preparation never calls `media_publish`.
- Feed and photo Stories are supported, with manual or per-account automatic publication.
- Spanish text is normalized and sent as JSON UTF-8.

## Facebook publisher

- Generic multi-page integration using `https://graph.facebook.com`.
- Secure encrypted Page tokens, connection checks, feed images and photo Stories.
- Durable ARQ preparation/publication states and per-account manual or automatic publication.
- Unit and E2E tests cover secret redaction, the unpublished-photo Story flow and Spanish UTF-8 text.

## Verified foundation slice — 2026-08-04

The repository contains a runnable Foundation Build slice. It is not yet the full
long-term product described by the canonical documentation. Remaining work includes
the complete management UI, richer workflow node catalog,
automated test coverage and CI execution.

### Delivered and verified

- Docker Compose starts API, worker, frontend, PostgreSQL and Redis.
- PostgreSQL and Redis use named persistent Docker volumes.
- Alembic applies migrations through `0018_workflow_schedules` on an empty database.
- The API has live and readiness probes; readiness confirmed PostgreSQL and Redis.
- First-run setup creates one administrator. A configured initial administrator is
  also supported by `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD`.
- Login, JWT access tokens, refresh-token rotation and logout are implemented.
- Authenticated provider discovery found four host Ollama models.
- The local provider catalog persists synchronized model records and authorized
  users can request an explicit model pull as a durable background task.
- Authenticated conversations are owner-scoped, stream through SSE and persist
  both messages after a real `llama3.2:3b` response.
- Conversations can be listed and deleted within their owner scope.
- Agent draft/version/publish endpoints are owner-scoped. Published agents execute
  their immutable prompt/model version through Ollama.
- RBAC seeds administrator, operator and viewer roles with a durable permission
  matrix. The first-run administrator receives the system-administrator role.
- Authorized administrators can list roles and users, create users, assign roles,
  and suspend or disable users while preserving the last active administrator.
- The filesystem tool exposes only UTF-8 read/write operations inside a persistent
  Docker volume sandbox. Writes are audited and path traversal is rejected.
- The HTTP tool uses an explicit host allowlist, blocks private/local destinations,
  enforces HTTPS, timeout and response limits, and audits every request.
- The restricted Python tool parses source before execution and runs it in a
  short-lived isolated interpreter with no application environment, a small
  standard-library allowlist, resource limits and a hard wall-clock timeout.
- Plugin manifests validate semantic versions, namespaced tool keys and tool risk
  declarations. Plugins are disabled by default and can be enabled, health-checked
  and disabled again without restarting the Core; lifecycle changes are audited.
- External Python plugin code uses one `docker_sandbox` container per execution.
  The backend and worker have no Docker socket mount; an internal, constrained
  Docker proxy provides only the lifecycle calls required by the fixed runtime.
  Each sandbox runs non-root with a read-only filesystem, no network, no Linux
  capabilities, no host mounts or global environment, fixed CPU/RAM/PID/time
  limits, and forced cleanup. `in_process` rejects external plugins.
- Durable background tasks use PostgreSQL for state, Redis/ARQ for dispatch and
  a worker for execution. A real smoke task completed successfully and users can
  retrieve their task history and progress. On worker startup, safe internal
  tasks and interrupted workflow runs are requeued; a cancellation is finalized,
  and non-idempotent provider pulls use a persisted bounded retry policy.
- API keys are hashed, scoped, revocable and audited. A limited key was rejected
  from an administrative endpoint with `403`.
- API request completion logs are emitted as JSON with timestamp, level, logger,
  request ID and correlation ID, while security and lifecycle actions remain in
  the durable audit-event stream.
- Persistent user-scoped memory supports namespace filtering, text search and
  deletion.
- Versioned workflow graphs validate node references and cycles, publish, enqueue
  durable runs and execute through ARQ. Agent nodes invoke the referenced
  owner-scoped published agent through Ollama in the worker.
- Workflow graphs reject unregistered node types. In addition to input, output,
  agent and condition nodes, they support declarative transforms, restricted Python
  a bounded delay, bounded list loops, one-time persistent schedules and a persisted human approval pause. Approval decisions are
  audited and only an explicit approved decision resumes the durable run.
- The React frontend builds and provides first-run setup, login and authenticated
  streaming chat. It also loads the authenticated conversation catalog and can
  restore messages from a selected persisted conversation. A streaming message
  announces its persistent identifier before generation, allowing the UI to
  cancel it durably rather than merely closing the browser connection. Chat
  messages render safe basic Markdown, copy fenced code blocks and regenerate
  from the preceding user message.
- The Agents screen supports creating a real draft agent with key, name and system
  prompt, then refreshes the owner-scoped catalog.
- The Workflows screen supports creating a workflow, opening a versioned graph,
  editing its JSON definition, creating a new version, publishing it and queuing
  a published version. It is an operational editor, not yet the visual node canvas.
- The Plugins screen registers a basic validated manifest and exposes the existing
  enable/disable lifecycle controls for authorized administrators.
- The UI also provides authenticated operational screens for persistent memory
  (create, search and delete), audit events, users/roles and Core/Ollama status.

### Verification evidence

- `docker compose config`: passed.
- `docker compose build api worker frontend`: passed.
- `docker compose up -d --force-recreate`: passed; all five services were running.
- `alembic current`: `0015_memory_scopes (head)`.
- `GET /health/ready`: `200`, PostgreSQL, Redis and worker heartbeat true.
- Unauthenticated provider discovery: `401`.
- Authenticated provider discovery: four models returned.
- Provider catalog synchronization: four persistent records created from the
  installed Ollama models (`llama3.2:3b`, `nomic-embed-text:latest`,
  `qwen2.5-coder:14b`, `qwen3:8b`).
- Authenticated SSE chat: completion event received and two messages recovered.
- Chat cancellation API: an in-progress assistant message was persisted, marked
  `cancelled` through its owner-scoped endpoint, and recovered with that status.
- Frontend task actions: the compiled UI exposes cancellation for running tasks
  and retry for failed or cancelled tasks; the backend lifecycle was previously
  verified through its durable cancellation E2E.
- Published agent execution against `llama3.2:3b`: returned a real response.
- Structured agent output E2E: a published `llama3.2:3b` agent declared
  `answer` as a required JSON field and returned a validated object containing it.
- Structured-output schemas are checked as Draft 2020-12 JSON Schema when an
  agent is created or versioned; completed agent output is validated against the
  entire declared schema, not only its required fields.
- Agent lifecycle E2E: a published agent was deactivated without deleting its
  version history, and a later run was rejected with `409` as expected.
- Agent archival: an archive endpoint preserves the immutable versions and audit
  trail while removing the agent from the operational catalog.
- Authenticated background smoke task: `succeeded`.
- Task history: returned the durable smoke task with a `succeeded` state.
- Cooperative task cancellation E2E: a running durable diagnostic task moved to
  `cancelling`, the worker observed that state during its next checkpoint and
  finished it as `cancelled` without publishing a successful result.
- Worker recovery E2E: a durable `system.sleep` task deliberately recorded as
  `running` before a worker restart was requeued by startup recovery and reached
  `succeeded`; the disposable validation row was deleted afterward.
- Scoped memory: a global entry created by an administrator was visible to a
  separate viewer account, while ordinary entries remain owner-scoped.
- Workflow graph `input -> agent -> output`: published, dispatched through Redis,
  invoked a published `llama3.2:3b` agent in the worker, and completed with the
  real output `WORKFLOW_OK` stored durably.
- Workflow filesystem E2E: `input -> file_write -> file_read -> output` completed
  durably through ARQ and recovered the expected `workflow-file-ok` content from
  the persistent sandbox. The validation file and account were removed afterward.
- Workflow HTTP E2E: with a temporary explicit allowlist for `example.com`,
  `input -> http -> output` completed through ARQ with an HTTP `200` response.
  The allowlist was restored to its secure empty default immediately afterward.
- Scheduled workflow E2E: a published `input -> output` version was scheduled
  for a future UTC time; the worker dispatched it once and it completed as
  `succeeded` with the expected durable input/output. The temporary account and
  its cascaded data were removed afterward.
- Filesystem tool: a write/read round-trip returned `sandbox-ok`; traversal was
  rejected with `422` and a limited API key was rejected with `403`.
- HTTP tool: a local destination was rejected with `403` under the default deny
  policy.
- Restricted Python tool: `import math; print(math.sqrt(81))` returned `9.0` in
  the application container, while `import os` was rejected by policy.
- Approval workflow E2E: `input -> approval -> output` paused as
  `waiting_approval`, resumed only after an authenticated `approved` decision and
  completed as `succeeded`. The disposable validation account and all of its data
  were deleted afterward, returning setup to its initial state.
- RBAC seed: three roles, eleven permissions and seventeen role-permission grants.
- Access administration: an administrator created a viewer user and the viewer was
  correctly denied access to the user-management endpoint with `403`.
- Plugin lifecycle: a validated `generic-http` manifest was enabled, reported
  `healthy`, and then disabled successfully.
- Plugin sandbox: policy tests assert the non-root, read-only, no-network,
  no-bind-mount, no-capability, no-new-privileges and resource-limit container
  specification; an actual sandbox invocation is verified through the internal
  Docker proxy and force-cleaned after capturing its result.
- Rate limit: the 121st request in a one-minute route window returned `429`.
- Backend quality gate in a clean Python 3.12 container: `ruff check app tests`,
  `pytest -q` (25 passed) and `mypy app` (48 source files) passed.
- `frontend: npm run typecheck` and `npm run build`: passed.

The disposable validation account was removed afterward. The deployed UI is ready
for its real first-run administrator setup.

## Facebook publisher real validation

- Meta app `ALSEMA Page Publisher` was configured with `pages_manage_posts`,
  `pages_read_engagement` and `pages_show_list`.
- The authorization was limited to the existing `Cometa G` Page and business
  assets instead of granting access to future assets.
- The Page token was encrypted in ALSEMA and never written to repository files or
  application logs.
- The live connection check returned Page `Cometa G` with status `connected` and
  the authorizing user has the `CREATE_CONTENT` task.
- A real Facebook Story photo upload reached `ready` with photo ID
  `1674622741330875`. It remained unpublished (`post_id` and `published_at` are
  empty) so technical validation did not create visible test content.
- The stored Spanish caption was verified from PostgreSQL as valid UTF-8 bytes.
- Automatic publication is enabled for the registered Page; approved future feed
  and Story jobs continue from `ready` to `published` without a manual click.

## Active next work

1. Automated API tests, linting and CI execution.
2. Complete user-facing management workflows for agents, workflows, plugins,
   tasks, logs and configuration.
3. Remaining documented workflow nodes and resilient task lifecycle features.

## Known Foundation Build gaps

The repository is runnable, but it must not yet be represented as a completed
Foundation Build. The remaining acceptance gaps are: full UI workflows for agent
and a visual workflow canvas, plus the documented automated
backend and browser test suites. These are tracked explicitly so a later delivery
audit can verify them rather than infer completion from the current runnable slice.
