# 13 — Workflow and Task Engine

## Objetivo

Definir dos responsabilidades relacionadas pero separadas:

- **Workflow Engine:** describe y ejecuta grafos de pasos.
- **Task Engine:** garantiza ejecución durable, progreso, cancelación, reintentos y recuperación.

Un workflow puede crear una tarea, pero una tarea no necesariamente pertenece a un workflow.

## Alcance del Foundation Build

Workflow Engine funcional con nodos básicos:

- input;
- output;
- LLM/agent;
- tool;
- HTTP mediante plugin;
- filesystem mediante plugin;
- condition;
- transform JSON;
- delay acotado;
- manual approval;

Task Engine funcional:

- persistencia durable;
- ARQ + Redis como transporte de ejecución;
- estados;
- prioridad básica;
- progreso;
- reintentos;
- cancelación cooperativa;
- idempotencia;
- logs/eventos;
- recuperación tras reinicio.

Fuera de alcance:

- reemplazar n8n;
- editor de expresiones arbitrarias;
- ejecución distribuida multi-región;
- cron avanzado empresarial;
- compensaciones automáticas universales;
- loops ilimitados;
- subworkflows recursivos sin límites.

## Workflow Definition

Un workflow es una identidad estable con versiones inmutables.

Cada versión contiene:

- JSON Schema de entrada;
- JSON Schema de salida;
- nodos;
- conexiones;
- configuración de errores;
- límites de ejecución;
- metadatos de UI.

Ejemplo conceptual:

```json
{
  "schema_version": "1",
  "nodes": [
    {"id": "input", "type": "core.input", "config": {}},
    {"id": "agent", "type": "core.agent", "config": {"agent_key": "rewriter"}},
    {"id": "output", "type": "core.output", "config": {}}
  ],
  "edges": [
    {"source": "input", "target": "agent"},
    {"source": "agent", "target": "output"}
  ]
}
```

## Validación del grafo

Antes de publicar:

- IDs únicos;
- tipos de nodo registrados;
- schemas válidos;
- conexiones válidas;
- entrada y salida presentes;
- ausencia de ciclos, salvo nodo de loop explícito futuro;
- configuración requerida completa;
- permisos disponibles;
- límites razonables;
- nodos deshabilitados detectados;
- referencias de agente, herramienta y plugin resolubles.

Foundation Build ejecuta grafos dirigidos acíclicos.

## Contrato de nodo

Todo nodo implementa:

- `type_key`
- `input_schema`
- `output_schema`
- `validate_config()`
- `execute(context, input)`
- `risk_level`
- `supports_retry`
- `is_idempotent`
- `timeout_seconds`

El contexto expone solo:

- workflow_run_id;
- task_id;
- actor;
- logger;
- secret resolver limitado;
- cancel token;
- event emitter;
- servicios públicos autorizados.

## Datos entre nodos

Cada salida debe ser JSON serializable. Los blobs grandes se guardan como artifacts y se pasan por referencia.

No almacenar archivos binarios grandes dentro de `workflow_node_runs.output`.

Formato de referencia:

```json
{
  "artifact_id": "uuid",
  "media_type": "application/json",
  "size_bytes": 1234
}
```

## Expresiones

Foundation Build soporta referencias simples, no código arbitrario:

- `$.input.title`
- `$.nodes.agent.output.summary`
- valores literales;
- plantillas de texto acotadas.

No usar `eval`, JavaScript arbitrario ni Python arbitrario para mapear datos.

## Condition Node

Operadores permitidos:

- equals / not_equals;
- contains;
- exists;
- greater_than / less_than;
- and / or;
- matches con regex limitada y timeout.

La condición produce una rama nombrada. Las ramas deben validarse antes de publicar.

## Manual Approval

Una ejecución puede entrar en `waiting_approval`.

Debe registrar:

- acción propuesta;
- riesgo;
- datos redactados;
- usuario o rol autorizado;
- vencimiento;
- decisión;
- comentario opcional.

Al vencer, aplicar la política configurada: cancelar o fallar. Nunca aprobar automáticamente.

## Estados de WorkflowRun

- `queued`
- `running`
- `waiting_approval`
- `succeeded`
- `failed`
- `cancel_requested`
- `cancelled`
- `partially_succeeded`

Foundation Build debe evitar `partially_succeeded` salvo que exista una política explícita y visible.

## Estados de Task

- `pending`
- `queued`
- `running`
- `retrying`
- `waiting`
- `succeeded`
- `failed`
- `cancel_requested`
- `cancelled`
- `expired`

Las transiciones se validan mediante una máquina de estados. No actualizar strings libremente.

## Creación durable de tareas

Flujo obligatorio:

1. validar request;
2. crear fila `tasks` en PostgreSQL;
3. commit;
4. encolar ID en ARQ;
5. responder `202 Accepted`.

Si falla el enqueue después del commit, un reconciliador detecta tareas pendientes no encoladas y reintenta.

## Ejecución

El worker:

1. carga la tarea con lock apropiado;
2. verifica estado y cancelación;
3. incrementa intento;
4. marca inicio;
5. ejecuta handler registrado;
6. guarda checkpoints;
7. emite progreso;
8. guarda resultado o error;
9. marca estado final.

No confiar únicamente en el estado interno de ARQ.

## Idempotencia

Endpoints de creación de trabajos aceptan `Idempotency-Key`.

Reglas:

- misma key + mismo actor + mismo tipo y payload equivalente devuelve la tarea existente;
- misma key con payload incompatible devuelve `409 IDEMPOTENCY_CONFLICT`;
- las keys tienen retención configurable;
- nodos no idempotentes no se reintentan automáticamente sin política explícita.

## Reintentos

Clasificación:

- error transitorio: retry con backoff y jitter;
- error permanente: falla inmediata;
- validación: no retry;
- proveedor no disponible: retry limitado;
- timeout: según idempotencia;
- cancelación: no retry.

La política debe ser visible en UI y logs.

## Cancelación

Cancelación cooperativa:

- el usuario solicita cancelación;
- se marca `cancel_requested_at`;
- worker comprueba token entre pasos;
- clientes HTTP cancelan cuando sea posible;
- el resultado parcial se conserva como diagnóstico;
- estado final `cancelled`.

No afirmar cancelación instantánea durante una llamada externa que no la soporta.

## Progreso

Campos:

- current;
- total;
- percentage derivado;
- stage;
- message;
- updated_at.

Para tareas sin total conocido, mostrar progreso indeterminado con etapa actual.

Los eventos se transmiten por SSE o WebSocket y se persisten en `task_events`.

## Recuperación

Al iniciar:

- detectar tareas `running` cuyo heartbeat venció;
- clasificarlas como recuperables o fallidas;
- reenviar tareas idempotentes;
- no repetir acciones externas no idempotentes sin intervención;
- registrar evento de recuperación.

## Scheduler

Foundation Build puede incluir programación simple:

- ejecución única futura;
- cron básico validado;
- timezone explícita;
- habilitar/deshabilitar.

Si su implementación pone en riesgo el Foundation Build, puede diferirse, pero los contratos deben quedar preparados. La ejecución manual y por API es obligatoria.

## Editor visual

Características mínimas:

- canvas oscuro;
- catálogo lateral de nodos;
- drag and drop;
- conexiones visibles;
- panel de configuración;
- validación inmediata;
- guardar borrador;
- publicar versión;
- ejecutar prueba;
- ver ejecución y logs por nodo.

No priorizar animaciones sobre legibilidad.

## API mínima

Workflows:

- `GET /api/v1/workflows`
- `POST /api/v1/workflows`
- `GET /api/v1/workflows/{id}`
- `POST /api/v1/workflows/{id}/versions`
- `POST /api/v1/workflows/{id}/versions/{version}/validate`
- `POST /api/v1/workflows/{id}/versions/{version}/publish`
- `POST /api/v1/workflows/{id}/run`
- `GET /api/v1/workflow-runs/{id}`

Tasks:

- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{id}`
- `POST /api/v1/tasks/{id}/cancel`
- `POST /api/v1/tasks/{id}/retry`
- `GET /api/v1/tasks/{id}/events`

## Seguridad

- validar permisos de cada nodo antes de iniciar;
- volver a validar al ejecutar acciones críticas;
- no guardar secretos en el grafo;
- no permitir URLs arbitrarias sin política del plugin HTTP;
- aprobaciones para acciones de riesgo;
- límites de cantidad de nodos, tamaño de payload y duración;
- auditoría de publicación y ejecución.

## Criterios de aceptación

- Crear workflow borrador de tres nodos.
- Validar y publicar una versión.
- Ejecutarlo como tarea durable.
- Ver progreso por nodo.
- Reiniciar el worker y recuperar una tarea segura.
- Cancelar entre nodos.
- Reintentar un error transitorio.
- Evitar duplicado mediante idempotency key.
- Pausar por aprobación manual.
- Rechazar un grafo cíclico o un nodo inexistente.
