# 06 — API Conventions

## Objetivo

Establecer contratos consistentes para las APIs públicas e internas de ALSEMA AI CORE. Toda implementación backend, SDK, plugin o cliente debe respetar estas reglas salvo que un ADR aprobado indique lo contrario.

## Principios

- API versionada desde el primer día.
- Recursos y acciones previsibles.
- Errores estructurados.
- Idempotencia en operaciones críticas.
- Streaming cuando mejora la experiencia, no como sustituto de respuestas normales.
- Contratos explícitos mediante OpenAPI y JSON Schema.
- Ninguna respuesta depende del formato interno de SQLAlchemy.

## Base path

```text
/api/v1
```

Endpoints de infraestructura no versionados:

```text
/health
/ready
/metrics
/docs
/openapi.json
```

## Formato

- JSON UTF-8 para REST.
- `multipart/form-data` solo para cargas de archivos.
- WebSocket o Server-Sent Events para streaming según el caso.
- Fechas ISO 8601 en UTC con sufijo `Z`.
- UUIDs como strings.
- Nombres de campos en `snake_case`.

## Recursos iniciales

```text
/api/v1/auth
/api/v1/users
/api/v1/roles
/api/v1/api-keys
/api/v1/providers
/api/v1/models
/api/v1/inference-profiles
/api/v1/conversations
/api/v1/messages
/api/v1/agents
/api/v1/tools
/api/v1/plugins
/api/v1/workflows
/api/v1/tasks
/api/v1/memory
/api/v1/logs
/api/v1/audit-events
/api/v1/system
```

## Respuesta exitosa

Los recursos simples pueden devolverse directamente.

```json
{
  "id": "b5f1d6c0-...",
  "name": "Ollama Local",
  "status": "enabled"
}
```

Las colecciones usan envelope:

```json
{
  "items": [],
  "page": {
    "cursor": null,
    "next_cursor": null,
    "has_more": false,
    "total": 0
  }
}
```

El total puede omitirse cuando calcularlo sea costoso.

## Errores

Formato obligatorio:

```json
{
  "error": {
    "code": "provider_unavailable",
    "message": "El proveedor no está disponible.",
    "details": {},
    "request_id": "req_...",
    "correlation_id": "cor_..."
  }
}
```

Reglas:

- `code` es estable y apto para máquinas.
- `message` es legible y no expone secretos.
- `details` contiene errores de validación o contexto seguro.
- Todo error 5xx incluye `request_id`.
- Los stack traces nunca salen por API en producción.

## Códigos HTTP

- `200 OK`: lectura o actualización exitosa.
- `201 Created`: recurso creado.
- `202 Accepted`: tarea asíncrona aceptada.
- `204 No Content`: eliminación o acción sin cuerpo.
- `400 Bad Request`: solicitud semánticamente inválida.
- `401 Unauthorized`: falta autenticación válida.
- `403 Forbidden`: autenticado sin permiso.
- `404 Not Found`: recurso inexistente o no visible.
- `409 Conflict`: versión, estado o idempotencia en conflicto.
- `413 Payload Too Large`: límite excedido.
- `422 Unprocessable Entity`: validación de schema.
- `429 Too Many Requests`: rate limit.
- `500 Internal Server Error`: fallo no controlado.
- `502 Bad Gateway`: proveedor externo falló.
- `503 Service Unavailable`: servicio temporalmente no disponible.
- `504 Gateway Timeout`: timeout de proveedor o herramienta.

## Paginación

Preferir cursor pagination:

```text
?limit=50&cursor=<opaque>
```

- Límite por defecto: 50.
- Máximo general: 200.
- El cursor es opaco para el cliente.
- Listados administrativos pequeños pueden usar `offset` si se documenta.

## Filtrado y orden

```text
?status=active
?provider_id=<uuid>
?sort=-created_at,name
?search=qwen
```

- Prefijo `-` indica descendente.
- Los filtros admitidos deben figurar en OpenAPI.
- No implementar un lenguaje de consultas arbitrario en v1.

## Idempotencia

Operaciones mutables expuestas a clientes externos aceptan:

```text
Idempotency-Key: <string única>
```

Aplicar al menos a:

- creación de tareas;
- ejecución de workflows;
- envío de mensajes;
- creación de memorias por integración;
- operaciones futuras con efectos externos.

La respuesta se conserva durante una ventana configurable.

## Concurrencia optimista

Recursos versionados pueden exponer:

```text
ETag: "version-7"
If-Match: "version-7"
```

Un conflicto devuelve `409` o `412` según el contrato elegido en implementación.

## Autenticación

### Web

Cookies seguras para access/refresh según el modelo de seguridad.

### API clients

```text
Authorization: Bearer aas_...
```

Nunca aceptar credenciales en query string.

## Correlación

El cliente puede enviar:

```text
X-Correlation-ID: <uuid o string válida>
```

Si falta, el servidor crea una. Se devuelve en headers y se propaga a tareas, logs y eventos.

## Chat y mensajes

### Crear conversación

```http
POST /api/v1/conversations
```

### Enviar mensaje

```http
POST /api/v1/conversations/{conversation_id}/messages
Idempotency-Key: ...
```

Respuesta síncrona si no hay streaming:

```json
{
  "message_id": "...",
  "task_id": "...",
  "status": "queued"
}
```

### Streaming

Canal recomendado:

```text
/api/v1/conversations/{conversation_id}/stream
```

Eventos normalizados:

```json
{"type":"message.started","message_id":"..."}
{"type":"message.delta","message_id":"...","delta":"texto"}
{"type":"tool.requested","execution_id":"...","tool":"read_file"}
{"type":"tool.completed","execution_id":"..."}
{"type":"message.completed","message_id":"...","usage":{}}
{"type":"message.failed","message_id":"...","error":{}}
```

El cliente debe poder reconectarse usando un cursor o último event ID cuando sea viable.

## Tareas

### Crear o disparar tarea

Devuelve `202`:

```json
{
  "task_id": "...",
  "status": "queued",
  "links": {
    "self": "/api/v1/tasks/...",
    "events": "/api/v1/tasks/.../events"
  }
}
```

### Progreso

```json
{
  "status": "running",
  "progress": {
    "current": 42,
    "total": 100,
    "percentage": 42,
    "message": "Procesando lote 5 de 10"
  }
}
```

### Cancelación

```http
POST /api/v1/tasks/{task_id}/cancel
```

La cancelación es una solicitud cooperativa, no garantía instantánea.

## Versionado de agentes y workflows

- `Agent` y `Workflow` son identidades estables.
- Las versiones se crean mediante endpoints explícitos.
- Publicar una versión es una acción auditable.

Ejemplo:

```http
POST /api/v1/agents/{agent_id}/versions
POST /api/v1/agents/{agent_id}/versions/{version_id}/publish
```

No usar `PUT` para mutar snapshots publicados.

## Archivos

Flujo inicial:

```http
POST /api/v1/files
GET /api/v1/files/{file_id}
DELETE /api/v1/files/{file_id}
```

La API devuelve IDs y metadatos, no rutas del host.

## Health endpoints

### `/health`

Confirma que el proceso responde.

### `/ready`

Verifica dependencias obligatorias:

- PostgreSQL;
- Redis;
- migraciones;
- worker cuando corresponda.

Ollama puede reportarse degradado sin impedir el arranque del panel, pero el chat indicará indisponibilidad.

## OpenAPI

- Todos los endpoints públicos documentados.
- Schemas con ejemplos útiles.
- Operaciones con `operation_id` estable.
- Tags por contexto delimitado.
- Errores comunes documentados.
- Generación futura de SDK basada en OpenAPI.

## Compatibilidad

Dentro de `/api/v1`:

- Se pueden agregar campos opcionales.
- No se renombran ni eliminan campos existentes sin nueva versión.
- No se cambia la semántica de enums sin migración.
- Los nuevos valores de enum deben ser tolerables por clientes o implican nueva versión.

## Límites iniciales configurables

- JSON request: 2 MB.
- Archivo individual: 25 MB.
- Mensaje de chat: 100.000 caracteres.
- Página: máximo 200 elementos.
- Timeout HTTP general: 30 segundos.
- Inferencia y tareas largas: gestionadas asíncronamente.

Los valores finales deben residir en configuración, no hardcodearse en handlers.
