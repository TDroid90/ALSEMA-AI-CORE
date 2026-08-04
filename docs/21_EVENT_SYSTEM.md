# 21 — Internal Event System

## Propósito

Definir eventos internos estables para desacoplar módulos dentro del monolito modular sin introducir un broker distribuido innecesario.

## Principios

- Los eventos describen hechos ocurridos, no órdenes ambiguas.
- Los nombres se versionan cuando cambia el contrato.
- Los payloads son pequeños y referencian entidades por ID.
- La publicación no reemplaza transacciones de dominio.
- Los consumidores deben ser idempotentes.
- Los eventos sensibles respetan permisos y minimización de datos.

## Tipos

### Domain events

Se generan dentro de un módulo como consecuencia de una transición válida.

Ejemplos:

- `agent.created.v1`
- `agent.version_published.v1`
- `task.queued.v1`
- `task.completed.v1`
- `task.failed.v1`
- `provider.status_changed.v1`
- `model.catalog_synced.v1`
- `workflow.run_started.v1`
- `workflow.node_failed.v1`
- `memory.created.v1`

### Integration events

Se publicarán en el futuro hacia clientes o plugins externos. En v1 se registran contratos, pero no se expone un bus público general.

### UI events

Actualizaciones efímeras para WebSocket/SSE, derivadas de estado persistente.

## Envelope

```json
{
  "event_id": "uuid",
  "event_type": "task.completed.v1",
  "occurred_at": "UTC ISO-8601",
  "producer": "tasks",
  "correlation_id": "uuid",
  "causation_id": "uuid|null",
  "actor_id": "uuid|null",
  "aggregate_type": "task",
  "aggregate_id": "uuid",
  "payload": {},
  "metadata": {}
}
```

## Entrega interna

v1 utilizará un dispatcher en proceso para efectos síncronos simples y una tabla outbox para efectos que deban sobrevivir reinicios.

Reglas:

- No ejecutar llamadas externas dentro de la transacción principal.
- Persistir evento outbox en la misma transacción que el cambio de estado.
- Worker procesa outbox con retries.
- Marcar entrega y errores.
- Limpiar registros según retención.

## Orden

No garantizar orden global.

Cuando un consumidor requiera orden por agregado, utilizar versión o secuencia del agregado y rechazar eventos fuera de orden de forma controlada.

## Idempotencia

Cada consumidor conserva o deriva una clave idempotente basada en `event_id` y nombre del consumidor.

## Fallos

- Retry con backoff.
- Límite de intentos.
- Estado dead-letter interno persistente.
- UI administrativa para inspección y reintento.
- Nunca descartar silenciosamente.

## Compatibilidad

Agregar campos opcionales es compatible.

Renombrar, eliminar o cambiar semántica requiere nueva versión de evento.

## Seguridad

- No incluir secretos.
- No incluir contenido completo si basta un ID.
- Verificar permisos antes de emitir eventos a conexiones de usuario.
- Los plugins reciben solo eventos declarados en su manifest.

## Criterios de aceptación

- Un cambio de estado crítico produce evento auditable.
- El outbox sobrevive reinicio.
- Un consumidor repetido no duplica efecto.
- Un fallo queda visible y puede reintentarse.
- Los eventos de UI se correlacionan con estado persistente.
