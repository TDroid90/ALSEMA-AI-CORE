# 25 — Superficie OpenAPI del Foundation Build

## Objetivo

Definir los recursos y operaciones mínimas que deben quedar operativas en `/api/v1`. Este documento fija comportamiento, no obliga a copiar literalmente nombres internos de clases.

## Convenciones

- JSON UTF-8.
- IDs UUID.
- Fechas ISO 8601 en UTC.
- Paginación por cursor cuando el volumen pueda crecer.
- Mutaciones idempotentes mediante `Idempotency-Key` cuando corresponda.
- Errores con `code`, `message`, `details`, `request_id`.
- Nunca devolver secretos completos.

## Sistema

### `GET /health/live`
Indica que el proceso responde.

### `GET /health/ready`
Comprueba base de datos, Redis y migraciones. Ollama puede figurar degradado sin impedir el acceso administrativo.

### `GET /system/status`
Resumen autenticado de servicios, workers, proveedor, versión y capacidad disponible.

## Instalación inicial

### `GET /setup/status`
Informa si el sistema requiere configuración inicial.

### `POST /setup/initialize`
Crea el primer administrador únicamente cuando no existe instalación previa. Usa variables de entorno o token de bootstrap de un solo uso.

## Autenticación

### `POST /auth/login`
### `POST /auth/refresh`
### `POST /auth/logout`
### `GET /auth/me`
### `PATCH /auth/me`

El refresh token debe rotar y poder revocarse.

## Usuarios y roles

### `GET /users`
### `POST /users`
### `GET /users/{id}`
### `PATCH /users/{id}`
### `POST /users/{id}/disable`
### `POST /users/{id}/enable`
### `GET /roles`
### `POST /roles`
### `PATCH /roles/{id}`

## API Keys

### `GET /api-keys`
### `POST /api-keys`
### `DELETE /api-keys/{id}`

El valor completo se muestra una sola vez al crearla.

## Proveedores y modelos

### `GET /providers`
### `POST /providers`
### `GET /providers/{id}`
### `PATCH /providers/{id}`
### `POST /providers/{id}/test`
### `POST /providers/{id}/enable`
### `POST /providers/{id}/disable`
### `GET /providers/{id}/models`
### `POST /providers/{id}/models/sync`

Para Ollama:

### `POST /providers/{id}/models/pull`
### `GET /providers/{id}/models/pull/{task_id}`
### `DELETE /providers/{id}/models/{model_id}`

Toda descarga debe requerir acción explícita y mostrar tamaño cuando el proveedor lo informe.

## Agentes

### `GET /agents`
### `POST /agents`
### `GET /agents/{id}`
### `PATCH /agents/{id}`
### `DELETE /agents/{id}`
### `POST /agents/{id}/versions`
### `GET /agents/{id}/versions`
### `POST /agents/{id}/versions/{version_id}/publish`
### `POST /agents/{id}/duplicate`
### `POST /agents/{id}/run`

Las ejecuciones usan siempre una versión inmutable.

## Conversaciones y chat

### `GET /conversations`
### `POST /conversations`
### `GET /conversations/{id}`
### `PATCH /conversations/{id}`
### `DELETE /conversations/{id}`
### `GET /conversations/{id}/messages`
### `POST /conversations/{id}/messages`
### `POST /conversations/{id}/regenerate`
### `POST /conversations/{id}/stop`

Streaming:

- SSE recomendado para tokens y eventos simples.
- WebSocket reservado para sesiones bidireccionales que lo necesiten.

Eventos mínimos:

```text
message.started
message.delta
message.tool_requested
message.tool_result
message.completed
message.failed
message.cancelled
```

## Herramientas

### `GET /tools`
### `GET /tools/{id}`
### `POST /tools/{id}/test`

La prueba de herramientas con riesgo medio o alto sigue la política de aprobación.

## Plugins

### `GET /plugins`
### `POST /plugins/install`
### `GET /plugins/{id}`
### `POST /plugins/{id}/activate`
### `POST /plugins/{id}/deactivate`
### `DELETE /plugins/{id}`
### `GET /plugins/{id}/health`
### `GET /plugins/{id}/permissions`

## Workflows

### `GET /workflows`
### `POST /workflows`
### `GET /workflows/{id}`
### `PATCH /workflows/{id}`
### `DELETE /workflows/{id}`
### `POST /workflows/{id}/versions`
### `POST /workflows/{id}/versions/{version_id}/validate`
### `POST /workflows/{id}/versions/{version_id}/publish`
### `POST /workflows/{id}/run`
### `GET /workflow-runs/{run_id}`
### `POST /workflow-runs/{run_id}/cancel`
### `POST /workflow-runs/{run_id}/retry`

## Tareas

### `GET /tasks`
### `GET /tasks/{id}`
### `POST /tasks/{id}/cancel`
### `POST /tasks/{id}/retry`
### `GET /tasks/{id}/events`
### `GET /tasks/{id}/logs`

## Aprobaciones

### `GET /approvals`
### `GET /approvals/{id}`
### `POST /approvals/{id}/approve`
### `POST /approvals/{id}/reject`

Toda decisión queda auditada.

## Memoria

### `GET /memory`
### `POST /memory`
### `GET /memory/{id}`
### `PATCH /memory/{id}`
### `DELETE /memory/{id}`
### `POST /memory/search`

La API aplica siempre el ámbito autorizado del usuario/proyecto/conversación.

## Logs y auditoría

### `GET /logs`
### `GET /audit-events`
### `GET /audit-events/{id}`

Los filtros incluyen fecha, nivel, módulo, actor, tarea, agente y plugin.

## Configuración

### `GET /settings`
### `PATCH /settings`
### `GET /secrets`
### `POST /secrets`
### `DELETE /secrets/{id}`

`GET /secrets` solo devuelve metadatos y estado, jamás valores.

## Ejemplo de error

```json
{
  "error": {
    "code": "provider_unavailable",
    "message": "El proveedor Ollama no está disponible.",
    "details": {"provider_id": "..."},
    "request_id": "..."
  }
}
```

## Criterios de aceptación

- OpenAPI se genera desde contratos reales.
- Todos los endpoints declaran permisos y errores posibles.
- Los ejemplos de la documentación pasan validación.
- El frontend consume un cliente TypeScript generado o derivado del esquema.
- Los cambios incompatibles requieren nueva versión de API o ADR explícito.
