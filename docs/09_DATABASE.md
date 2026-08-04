# 09 — Database Architecture

## Propósito

Este documento define la persistencia transaccional de ALSEMA AI CORE para el Foundation Build v1.0. PostgreSQL será la fuente de verdad para estado durable. Redis se utilizará exclusivamente para coordinación efímera, colas, locks, caché acotada y publicación de eventos de tiempo real.

## Principios

1. PostgreSQL conserva el estado que no puede perderse.
2. Redis nunca será la única copia de una tarea, conversación, configuración o auditoría.
3. Todas las tablas de negocio usan UUID.
4. Todas las fechas se almacenan en UTC con zona horaria.
5. Las migraciones se realizan exclusivamente con Alembic.
6. No se modifica el esquema manualmente en producción.
7. Los secretos no se almacenan en texto plano.
8. Las entidades configurables relevantes se versionan.
9. Las eliminaciones destructivas requieren una política explícita.
10. Los nombres de tablas y columnas se escriben en `snake_case` y en inglés.

## Convenciones generales

Todas las entidades principales deben incluir, cuando corresponda:

- `id UUID PRIMARY KEY`
- `created_at TIMESTAMPTZ NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`
- `created_by UUID NULL`
- `updated_by UUID NULL`
- `deleted_at TIMESTAMPTZ NULL` para soft delete
- `version INTEGER NOT NULL DEFAULT 1` para control optimista cuando exista edición concurrente

Los eventos y logs son append-only y no usan `updated_at` salvo necesidad técnica documentada.

## Extensiones PostgreSQL

Foundation Build:

- `pgcrypto` para UUID y funciones criptográficas auxiliares.
- `citext` para correos electrónicos y nombres que deban compararse sin distinguir mayúsculas.

Fuera del Foundation Build, sujeto a ADR:

- `vector` para embeddings y búsqueda semántica.
- extensiones de observabilidad o particionamiento avanzado.

## Esquemas lógicos

Para v1 puede utilizarse el esquema PostgreSQL `public`, pero el código debe agrupar las tablas por módulos. No se crearán múltiples schemas físicos hasta demostrar una necesidad real.

Módulos persistentes:

- identity
- access
- providers
- models
- conversations
- agents
- tools
- plugins
- workflows
- tasks
- memory
- audit
- settings

## Identity y acceso

### `users`

- `id`
- `email CITEXT UNIQUE NOT NULL`
- `display_name VARCHAR(120) NOT NULL`
- `password_hash TEXT NOT NULL`
- `status VARCHAR(30) NOT NULL`
- `is_system_admin BOOLEAN NOT NULL DEFAULT FALSE`
- `last_login_at TIMESTAMPTZ NULL`
- timestamps y auditoría

Estados permitidos: `pending`, `active`, `disabled`, `locked`.

### `roles`

- `id`
- `key VARCHAR(80) UNIQUE NOT NULL`
- `name VARCHAR(120) NOT NULL`
- `description TEXT NULL`
- `is_system BOOLEAN NOT NULL DEFAULT FALSE`

### `permissions`

- `id`
- `key VARCHAR(120) UNIQUE NOT NULL`
- `description TEXT NOT NULL`
- `risk_level VARCHAR(20) NOT NULL`

Formato recomendado: `resource.action`, por ejemplo `agents.create`, `tools.execute`, `system.manage`.

### `user_roles`

Clave primaria compuesta por `user_id`, `role_id`.

### `role_permissions`

Clave primaria compuesta por `role_id`, `permission_id`.

### `refresh_tokens`

- `id`
- `user_id`
- `token_hash`
- `family_id UUID NOT NULL`
- `expires_at`
- `revoked_at`
- `replaced_by_id NULL`
- `user_agent NULL`
- `ip_address INET NULL`

Nunca almacenar el token original.

### `api_keys`

- `id`
- `owner_user_id`
- `name`
- `prefix`
- `secret_hash`
- `scopes JSONB`
- `last_used_at`
- `expires_at`
- `revoked_at`

## Proveedores y modelos

### `provider_connections`

Representa una instancia configurada de un proveedor.

- `id`
- `provider_type` — inicialmente `ollama`
- `name`
- `base_url`
- `encrypted_credentials JSONB NULL`
- `configuration JSONB NOT NULL DEFAULT '{}'`
- `status`
- `last_healthcheck_at`
- `last_healthcheck_result JSONB`
- timestamps

### `model_catalog`

Representa un modelo detectado o registrado.

- `id`
- `provider_connection_id`
- `external_id`
- `display_name`
- `capabilities JSONB`
- `context_window INTEGER NULL`
- `parameters JSONB`
- `size_bytes BIGINT NULL`
- `digest VARCHAR(255) NULL`
- `status`
- `last_seen_at`

Índice único: `(provider_connection_id, external_id)`.

### `inference_profiles`

Configuraciones reutilizables y versionadas.

- `id`
- `name`
- `description`
- `provider_connection_id`
- `model_catalog_id`
- `temperature NUMERIC(4,3)`
- `top_p NUMERIC(4,3)`
- `max_output_tokens INTEGER NULL`
- `timeout_seconds INTEGER`
- `options JSONB`
- `version`
- `is_active`

## Conversaciones

### `conversations`

- `id`
- `title`
- `owner_user_id`
- `agent_id NULL`
- `project_scope VARCHAR(120) NULL`
- `metadata JSONB`
- `archived_at NULL`
- timestamps

### `messages`

- `id`
- `conversation_id`
- `parent_message_id NULL`
- `role` — `system`, `user`, `assistant`, `tool`
- `content TEXT`
- `content_blocks JSONB`
- `status` — `pending`, `streaming`, `completed`, `failed`, `cancelled`
- `provider_connection_id NULL`
- `model_catalog_id NULL`
- `agent_version_id NULL`
- `prompt_tokens NULL`
- `completion_tokens NULL`
- `latency_ms NULL`
- `error_code NULL`
- timestamps

Índice: `(conversation_id, created_at)`.

### `message_events`

Eventos append-only de streaming, uso de herramienta y errores. Deben poder purgarse por política sin perder el mensaje final.

## Agentes

### `agents`

Identidad estable del agente.

- `id`
- `key UNIQUE`
- `name`
- `description`
- `status`
- `current_version_id NULL`
- timestamps

### `agent_versions`

- `id`
- `agent_id`
- `version_number INTEGER`
- `system_prompt TEXT`
- `inference_profile_id`
- `output_schema JSONB NULL`
- `memory_policy JSONB`
- `tool_policy JSONB`
- `runtime_policy JSONB`
- `change_note TEXT`
- `published_at NULL`
- `created_by`

Índice único: `(agent_id, version_number)`.

### `agent_tool_bindings`

- `agent_version_id`
- `tool_definition_id`
- `permission_mode`
- `configuration JSONB`

## Herramientas y plugins

### `tool_definitions`

- `id`
- `key UNIQUE`
- `name`
- `description`
- `plugin_id NULL`
- `input_schema JSONB`
- `output_schema JSONB`
- `risk_level`
- `execution_mode`
- `timeout_seconds`
- `is_enabled`
- `version`

### `tool_executions`

- `id`
- `task_id NULL`
- `message_id NULL`
- `tool_definition_id`
- `requested_by_user_id`
- `input_redacted JSONB`
- `output_redacted JSONB NULL`
- `status`
- `started_at`
- `completed_at NULL`
- `error_code NULL`
- `audit_event_id NULL`

### `plugins`

- `id`
- `key UNIQUE`
- `name`
- `version`
- `manifest JSONB`
- `status`
- `installed_at`
- `enabled_at NULL`
- `last_healthcheck_at NULL`

### `plugin_configs`

- `id`
- `plugin_id`
- `environment`
- `configuration JSONB`
- `encrypted_secrets JSONB`
- `version`

## Workflows

### `workflows`

- `id`
- `key UNIQUE`
- `name`
- `description`
- `status`
- `current_version_id NULL`
- timestamps

### `workflow_versions`

- `id`
- `workflow_id`
- `version_number`
- `graph JSONB`
- `input_schema JSONB`
- `output_schema JSONB`
- `published_at NULL`
- `created_by`

### `workflow_runs`

- `id`
- `workflow_version_id`
- `task_id`
- `trigger_type`
- `input JSONB`
- `output JSONB NULL`
- `status`
- timestamps

### `workflow_node_runs`

- `id`
- `workflow_run_id`
- `node_id`
- `node_type`
- `attempt INTEGER`
- `input_redacted JSONB`
- `output_redacted JSONB NULL`
- `status`
- `started_at`
- `completed_at NULL`
- `error JSONB NULL`

Índice único: `(workflow_run_id, node_id, attempt)`.

## Tareas

### `tasks`

- `id`
- `type`
- `queue_name`
- `status`
- `priority INTEGER`
- `progress_current BIGINT NULL`
- `progress_total BIGINT NULL`
- `progress_message TEXT NULL`
- `payload JSONB`
- `result JSONB NULL`
- `error JSONB NULL`
- `idempotency_key VARCHAR(255) NULL`
- `requested_by_user_id NULL`
- `parent_task_id NULL`
- `scheduled_at NULL`
- `started_at NULL`
- `completed_at NULL`
- `cancel_requested_at NULL`
- `attempt_count INTEGER NOT NULL DEFAULT 0`
- `max_attempts INTEGER NOT NULL DEFAULT 3`
- timestamps

Índice único parcial para `idempotency_key` cuando no sea nulo y la tarea no haya expirado según política.

### `task_events`

Append-only:

- `id BIGSERIAL`
- `task_id`
- `event_type`
- `payload JSONB`
- `created_at`

Índice `(task_id, id)` para streaming incremental.

## Memoria

### `memory_entries`

- `id`
- `scope_type` — `global`, `user`, `project`, `agent`, `conversation`
- `scope_id NULL`
- `kind`
- `title NULL`
- `content TEXT`
- `metadata JSONB`
- `source_type`
- `source_id NULL`
- `importance NUMERIC(4,3)`
- `expires_at NULL`
- timestamps

Foundation Build ofrece CRUD y búsqueda textual simple. Embeddings quedan fuera de alcance.

## Auditoría

### `audit_events`

Tabla append-only:

- `id UUID`
- `actor_type`
- `actor_id NULL`
- `action`
- `resource_type`
- `resource_id NULL`
- `result`
- `risk_level`
- `request_id`
- `ip_address INET NULL`
- `metadata_redacted JSONB`
- `created_at`

No incluir contraseñas, tokens, prompts secretos ni credenciales.

## Configuración

### `system_settings`

- `key PRIMARY KEY`
- `value JSONB`
- `value_type`
- `is_secret BOOLEAN`
- `version`
- timestamps

Los secretos verdaderos deben cifrarse antes de persistir o resolverse desde variables de entorno / secret store.

## Integridad y borrado

- Mensajes dependen de conversaciones con `ON DELETE CASCADE` únicamente si la política autoriza borrado definitivo.
- Auditoría nunca se elimina en cascada.
- Tareas y ejecuciones conservan referencias aunque el recurso original sea archivado.
- Modelos y proveedores se desactivan; no se eliminan mientras existan referencias históricas.
- Versiones publicadas de agentes y workflows son inmutables.

## Migraciones

Cada migración debe:

1. Tener nombre descriptivo.
2. Ser reversible cuando sea razonable.
3. Evitar operaciones bloqueantes sin documentar.
4. Incluir migración de datos si cambia una semántica existente.
5. Probarse desde una base vacía y desde la migración anterior.

No usar `create_all()` como mecanismo de producción.

## Retención

Foundation Build debe permitir configurar:

- días de retención de eventos de streaming;
- días de retención de logs técnicos;
- conservación indefinida de auditoría, salvo política explícita;
- purga de tareas y resultados voluminosos;
- archivado de conversaciones.

## Criterios de aceptación

- Alembic crea el esquema completo desde cero.
- Alembic puede revertir al menos la última migración no destructiva.
- Las restricciones impiden duplicados de correo, claves y versiones.
- Una tarea sobrevive al reinicio de API y worker.
- Un agente publicado conserva su versión histórica.
- Ningún secreto aparece en consultas normales, logs o respuestas de API.
