# ADR 0003 — ARQ y Redis para tareas en segundo plano

- Estado: Aceptada
- Fecha: 2026-08-04

## Contexto

ALSEMA AI CORE necesita ejecutar inferencias, descargas de modelos, workflows y operaciones potencialmente largas sin bloquear solicitudes HTTP.

La primera versión debe ser operable en una sola PC, sencilla de desplegar y suficientemente durable para recuperarse de errores comunes.

## Decisión

Usar ARQ sobre Redis como cola de tareas inicial.

PostgreSQL conserva el estado durable y auditable de cada tarea. Redis se utiliza para encolado, coordinación, locks, heartbeats y datos efímeros.

## Motivos

- Integración natural con Python async.
- Menor complejidad operativa que Celery para el alcance inicial.
- Redis ya es necesario para coordinación y cache.
- Adecuado para una instalación local y un número controlado de workers.
- Permite reintentos, scheduling básico y timeouts.

## Reglas

- Redis no es la única fuente de verdad del estado de una tarea.
- Antes de encolar se crea un registro durable en PostgreSQL.
- Cada ejecución debe ser idempotente o declarar explícitamente por qué no puede serlo.
- El worker actualiza heartbeat y progreso.
- La cancelación es cooperativa.
- Los reintentos usan backoff y límite.
- Un reconciliador detecta tareas huérfanas después de reinicios.

## Consecuencias

### Positivas

- Despliegue simple.
- Menos componentes.
- Buen encaje con FastAPI async.
- Curva operativa razonable.

### Negativas

- Menor ecosistema que Celery.
- Algunas necesidades avanzadas pueden requerir implementación propia.
- Si el volumen crece sustancialmente, la solución deberá reevaluarse.

## Alternativas consideradas

### Celery

Más maduro y amplio, pero agrega complejidad innecesaria en la primera versión.

### Dramatiq

Sólido, pero ARQ encaja mejor con el enfoque async elegido.

### BackgroundTasks de FastAPI

No ofrece durabilidad, reintentos ni recuperación adecuada.

## Revisión futura

Reevaluar si aparecen:

- múltiples nodos de workers;
- prioridades complejas;
- alto volumen sostenido;
- routing avanzado;
- requerimientos de broker distintos;
- garantías de entrega más estrictas.
