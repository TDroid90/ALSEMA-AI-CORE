# 17 — Observability

## Propósito

Definir cómo ALSEMA AI CORE registra, mide y expone su comportamiento para diagnosticar errores, analizar rendimiento y operar tareas largas con trazabilidad.

## Pilares

- Logs estructurados.
- Métricas.
- Trazas y correlación.
- Eventos de auditoría.
- Estado de salud.

## Correlation ID

Toda solicitud externa recibe o genera un `correlation_id`.

Debe propagarse a:

- logs;
- tareas;
- invocaciones a proveedores;
- ejecuciones de agentes;
- workflows;
- llamadas de herramientas;
- respuestas de error.

## Logs

Formato JSON en backend y workers.

Campos mínimos:

- timestamp UTC;
- level;
- service;
- module;
- message;
- correlation_id;
- user_id cuando corresponda;
- task_id;
- agent_execution_id;
- workflow_run_id;
- provider_id;
- duration_ms;
- error_code;
- exception_type;
- safe_context.

No registrar:

- contraseñas;
- tokens;
- API keys;
- secretos;
- prompts completos por defecto;
- contenido privado sin política explícita.

## Niveles

- DEBUG: solo desarrollo o diagnóstico temporal.
- INFO: hitos normales.
- WARNING: degradación recuperable.
- ERROR: operación fallida.
- CRITICAL: riesgo de indisponibilidad o integridad.

## Retención

- Configurable por tipo de log.
- Rotación local.
- Limpieza programada.
- Exportación futura mediante adaptadores.
- Auditoría con política de retención separada.

## Métricas mínimas

### HTTP

- requests totales;
- latencia;
- errores por código;
- conexiones activas;
- rate limit activado.

### Proveedores

- disponibilidad;
- latencia de primera respuesta;
- duración total;
- tokens aproximados si existen;
- solicitudes activas;
- errores por modelo;
- cancelaciones.

### Tareas

- queued;
- running;
- succeeded;
- failed;
- cancelled;
- retries;
- duración;
- tiempo en cola.

### Sistema

- CPU;
- RAM;
- espacio en disco;
- GPU y VRAM cuando sea posible;
- PostgreSQL;
- Redis;
- worker heartbeat.

## Health endpoints

### Liveness

Indica que el proceso responde. No debe depender de Ollama.

### Readiness

Valida dependencias necesarias para servir operaciones básicas:

- PostgreSQL;
- Redis cuando sea obligatorio;
- migraciones aplicadas;
- configuración válida.

Ollama puede estar degradado sin volver no disponible a todo el Core.

### Detailed health

Solo administradores. Muestra componentes y causas sanitizadas.

## Auditoría

Registrar acciones sensibles:

- login y cierre de sesión;
- fallos repetidos de autenticación;
- creación o revocación de API keys;
- cambios de roles;
- cambios de configuración;
- descargas y eliminaciones de modelos;
- aprobación de herramientas riesgosas;
- ejecución de shell o Python;
- instalación o activación de plugins;
- borrado de memoria;
- exportaciones.

## UI

La interfaz debe ofrecer:

- estado general;
- componentes saludables, degradados o caídos;
- tareas recientes;
- errores agrupados;
- filtros por módulo y fecha;
- detalle correlacionado;
- exportación de logs sanitizados.

## Alertas v1

No se requiere plataforma externa. Debe existir una capa de eventos para alertas futuras.

Alertas internas mínimas:

- disco bajo;
- PostgreSQL o Redis no disponible;
- worker sin heartbeat;
- tasa elevada de errores;
- Ollama fuera de línea;
- cola bloqueada;
- tarea excedida en tiempo.

## Criterios de aceptación

- Cada error API incluye correlation ID.
- Una tarea puede rastrearse desde API hasta worker y proveedor.
- Los healthchecks distinguen Core y proveedor.
- Los secretos no aparecen en logs de prueba.
- La UI muestra estado real y errores recientes.
- Existe auditoría para acciones administrativas.
