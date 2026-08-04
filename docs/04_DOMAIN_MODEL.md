# 04 — Domain Model

## Propósito

Este documento define las entidades, agregados, límites y relaciones fundamentales de ALSEMA AI CORE. El dominio debe permanecer independiente de FastAPI, SQLAlchemy, Ollama, React, Redis y cualquier proveedor externo.

## Principios de modelado

- El dominio expresa capacidades de la plataforma, no detalles de infraestructura.
- Cada agregado protege sus invariantes.
- Los identificadores son UUID generados por la aplicación.
- Todas las entidades persistentes incluyen `created_at`, `updated_at` y, cuando corresponda, `deleted_at`.
- Los estados se representan mediante enums explícitos.
- Las configuraciones extensibles pueden usar JSON validado, pero los campos críticos deben estar tipados.
- Ningún cliente empresarial aparece como entidad interna del Core.

## Contextos delimitados

### Identity & Access

Responsable de usuarios, sesiones, roles, permisos, API keys y auditoría de acceso.

### AI Providers

Responsable de proveedores, endpoints, modelos descubiertos, perfiles de inferencia y salud.

### Conversations

Responsable de conversaciones, mensajes, adjuntos, streaming y metadatos de ejecución.

### Agents

Responsable de definiciones de agentes, versiones, prompts, políticas, herramientas permitidas y memoria.

### Tools & Plugins

Responsable de registro de herramientas, contratos de entrada/salida, permisos y ejecución controlada.

### Workflows

Responsable de definiciones de workflows, nodos, conexiones, versiones y ejecuciones.

### Tasks

Responsable de trabajos asíncronos, progreso, reintentos, cancelación y resultados.

### Memory

Responsable de recuerdos persistentes, ámbitos, etiquetas, búsqueda y políticas de retención.

### Observability

Responsable de eventos, logs, métricas, trazas y auditoría funcional.

## Agregados principales

## User

Representa una identidad humana autorizada.

Campos:

- `id`
- `email`
- `display_name`
- `password_hash`
- `status`: `pending | active | suspended | disabled`
- `is_system_admin`
- `last_login_at`
- timestamps

Invariantes:

- El email normalizado es único.
- Un usuario deshabilitado no puede crear nuevas sesiones.
- Debe existir al menos un administrador activo.

## Role

Agrupa permisos reutilizables.

Campos:

- `id`
- `name`
- `slug`
- `description`
- `is_system_role`
- timestamps

Relaciones:

- muchos a muchos con `User`
- muchos a muchos con `Permission`

## Permission

Capacidad atómica expresada como `resource:action`, por ejemplo:

- `agents:read`
- `agents:write`
- `tools:execute`
- `system:admin`

## ApiKey

Credencial para clientes externos.

Campos:

- `id`
- `owner_user_id`
- `name`
- `prefix`
- `secret_hash`
- `scopes`
- `expires_at`
- `last_used_at`
- `revoked_at`

La clave completa solo se muestra al crearla.

## Provider

Configuración de un proveedor de IA.

Campos:

- `id`
- `name`
- `provider_type`: inicialmente `ollama`
- `base_url`
- `status`: `enabled | disabled | unhealthy`
- `capabilities`
- `configuration_encrypted`
- `health_checked_at`
- timestamps

Invariantes:

- Las credenciales nunca se almacenan en texto plano.
- Un proveedor deshabilitado no recibe nuevas ejecuciones.

## Model

Modelo descubierto o registrado dentro de un proveedor.

Campos:

- `id`
- `provider_id`
- `external_id`
- `display_name`
- `family`
- `capabilities`: texto, embeddings, visión, tools, JSON
- `context_window`
- `status`
- `metadata`
- `last_seen_at`

La combinación `provider_id + external_id` es única.

## InferenceProfile

Configuración reutilizable de inferencia.

Campos:

- `id`
- `name`
- `model_id`
- `temperature`
- `top_p`
- `top_k`
- `max_output_tokens`
- `context_policy`
- `structured_output_schema`
- `stop_sequences`

## Conversation

Contenedor de interacción.

Campos:

- `id`
- `owner_user_id`
- `title`
- `agent_version_id` opcional
- `model_id` opcional
- `status`: `active | archived | deleted`
- `settings`
- timestamps

## Message

Unidad inmutable dentro de una conversación.

Campos:

- `id`
- `conversation_id`
- `role`: `system | user | assistant | tool`
- `content`
- `content_parts`
- `parent_message_id`
- `sequence_number`
- `status`: `pending | streaming | complete | failed | cancelled`
- `token_usage`
- `latency_ms`
- `error_code`
- timestamps

Un mensaje completo no se edita: una edición crea una rama lógica o una nueva versión.

## Agent

Identidad estable de un agente reutilizable.

Campos:

- `id`
- `name`
- `slug`
- `description`
- `status`: `draft | active | archived`
- `current_version_id`
- timestamps

## AgentVersion

Snapshot inmutable de configuración.

Campos:

- `id`
- `agent_id`
- `version_number`
- `system_prompt`
- `inference_profile_id`
- `tool_policy`
- `memory_policy`
- `input_schema`
- `output_schema`
- `timeout_seconds`
- `created_by`
- `change_summary`

Una ejecución siempre referencia una versión concreta.

## ToolDefinition

Contrato de una herramienta.

Campos:

- `id`
- `plugin_id`
- `name`
- `slug`
- `description`
- `input_schema`
- `output_schema`
- `risk_level`: `safe | guarded | dangerous`
- `execution_mode`: `sync | async`
- `enabled`
- `timeout_seconds`

## ToolExecution

Registro de ejecución de herramienta.

Campos:

- `id`
- `tool_definition_id`
- `requested_by_user_id`
- `agent_run_id`
- `task_id`
- `input_redacted`
- `output_redacted`
- `status`
- `started_at`
- `finished_at`
- `error`

## Plugin

Paquete registrable de capacidades.

Campos:

- `id`
- `name`
- `slug`
- `version`
- `manifest`
- `status`: `installed | enabled | disabled | error`
- `health`
- `installed_at`

Los plugins no acceden directamente a tablas de otros contextos; utilizan contratos públicos.

## Workflow

Identidad estable de automatización.

Campos:

- `id`
- `name`
- `slug`
- `description`
- `status`: `draft | active | paused | archived`
- `current_version_id`
- timestamps

## WorkflowVersion

Snapshot inmutable del grafo.

Campos:

- `id`
- `workflow_id`
- `version_number`
- `nodes`
- `edges`
- `input_schema`
- `output_schema`
- `created_by`
- `change_summary`

## WorkflowRun

Ejecución concreta.

Campos:

- `id`
- `workflow_version_id`
- `trigger_type`: `manual | api | schedule | event`
- `triggered_by_user_id`
- `task_id`
- `status`
- `input`
- `output`
- `started_at`
- `finished_at`

## Task

Unidad durable de trabajo asíncrono.

Campos:

- `id`
- `task_type`
- `status`: `queued | running | succeeded | failed | cancelling | cancelled | retrying`
- `priority`
- `progress_current`
- `progress_total`
- `progress_message`
- `attempt`
- `max_attempts`
- `available_at`
- `started_at`
- `finished_at`
- `input_reference`
- `result_reference`
- `error_code`
- `error_message`
- `correlation_id`

Invariantes:

- Una tarea terminada no vuelve a `running`.
- La cancelación es cooperativa y debe dejar registro.
- Los reintentos deben ser idempotentes o estar protegidos por claves de idempotencia.

## MemoryEntry

Unidad persistente de memoria.

Campos:

- `id`
- `scope_type`: `global | user | project | agent | conversation`
- `scope_id`
- `kind`: `fact | preference | instruction | summary | artifact_reference`
- `content`
- `metadata`
- `importance`
- `source_type`
- `source_id`
- `expires_at`
- `deleted_at`
- timestamps

La memoria nunca debe mezclarse entre ámbitos sin autorización explícita.

## AuditEvent

Evento inmutable de seguridad y administración.

Campos:

- `id`
- `actor_type`
- `actor_id`
- `action`
- `resource_type`
- `resource_id`
- `result`
- `ip_address`
- `user_agent`
- `metadata_redacted`
- `created_at`

## Eventos de dominio iniciales

- `user.created`
- `user.disabled`
- `api_key.created`
- `provider.registered`
- `provider.health_changed`
- `model.discovered`
- `agent.version_published`
- `conversation.created`
- `message.completed`
- `task.queued`
- `task.progressed`
- `task.succeeded`
- `task.failed`
- `workflow.version_published`
- `workflow.run_started`
- `workflow.run_finished`
- `plugin.enabled`
- `plugin.failed`
- `memory.created`
- `memory.deleted`

## Reglas transversales

- Todos los comandos mutables aceptan `actor`, `correlation_id` e idempotency key cuando sean externos.
- Toda salida sensible pasa por redacción antes de logs o auditoría.
- Las configuraciones versionadas no se modifican in-place.
- Las eliminaciones funcionales usan soft delete; secretos y tokens revocados deben inutilizarse inmediatamente.
- Las referencias a archivos apuntan a un servicio de almacenamiento, nunca a rutas arbitrarias del host.
