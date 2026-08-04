# Matriz de trazabilidad — ALSEMA AI CORE

## Propósito

Este documento conecta requisitos, módulos, endpoints, pruebas y criterios de aceptación. Su objetivo es impedir que Codex marque una fase como terminada sin evidencia verificable.

## Reglas

- Todo requisito funcional debe tener al menos una implementación identificable y una prueba asociada.
- Todo endpoint público debe tener contrato OpenAPI, control de permisos y prueba de integración.
- Toda herramienta debe declarar riesgo, permisos, timeout, política de reintento y auditoría.
- Toda tarea durable debe tener estados, progreso, cancelación y recuperación.
- Ninguna fase puede considerarse finalizada con mocks permanentes en rutas de producción.

## Matriz principal

| ID | Requisito | Módulo responsable | Evidencia técnica | Prueba mínima | Estado Foundation |
|---|---|---|---|---|---|
| R-001 | Inicio con Docker Compose | platform/deployment | compose, env example, healthchecks | smoke test de stack | obligatorio |
| R-002 | Login administrador | identity | endpoint auth, JWT, sesión | E2E login/logout | obligatorio |
| R-003 | RBAC | identity/security | roles, permisos, guards | integración por rol | obligatorio |
| R-004 | Conexión Ollama | providers | adapter Ollama, healthcheck | integración real o test container controlado | obligatorio |
| R-005 | Listado de modelos | providers/models | API y UI | integración API + UI | obligatorio |
| R-006 | Chat con streaming | conversations/providers | SSE o WebSocket | E2E token streaming | obligatorio |
| R-007 | Historial persistente | conversations | PostgreSQL | integración CRUD | obligatorio |
| R-008 | Gestión de agentes | agents | CRUD y versiones | integración + E2E básico | obligatorio |
| R-009 | Tool calling | tools/agents | contratos y executor | unitarias + integración | obligatorio |
| R-010 | Riesgo y aprobación | tools/security | policy engine, approvals | integración allow/deny | obligatorio |
| R-011 | Tareas en segundo plano | tasks | ARQ, Redis, PostgreSQL | integración worker | obligatorio |
| R-012 | Progreso y cancelación | tasks/events | eventos y endpoint cancel | E2E tarea larga | obligatorio |
| R-013 | Reintentos | tasks | retry policy | integración fallo transitorio | obligatorio |
| R-014 | Plugins | plugins | manifest, registry, lifecycle | plugin HTTP/filesystem | obligatorio |
| R-015 | Workflows básicos | workflows | DAG, nodos, executor | E2E workflow básico | obligatorio |
| R-016 | Memoria persistente básica | memory | scopes, entries, search | integración aislamiento | obligatorio |
| R-017 | Logs estructurados | observability | JSON logs, correlation ID | prueba de formato | obligatorio |
| R-018 | Auditoría | audit/security | audit events | integración acciones sensibles | obligatorio |
| R-019 | Estado del sistema | system | health/readiness | smoke test | obligatorio |
| R-020 | Configuración segura | configuration | settings, secret encryption | integración redacción | obligatorio |
| R-021 | UI oscura coherente | frontend/design | tokens y componentes | visual/E2E básico | obligatorio |
| R-022 | OpenAPI versionada | api | `/api/v1`, schema | snapshot schema | obligatorio |
| R-023 | Rate limiting | api/security | middleware/policy | integración 429 | obligatorio |
| R-024 | API keys | identity | scopes, hashing | integración auth por key | obligatorio |
| R-025 | Backups documentados | operations | scripts y runbook | restauración controlada | obligatorio documental |

## Matriz de pantallas

| Pantalla | Fuente de datos | Acción crítica | Prueba |
|---|---|---|---|
| Login | identity API | crear sesión | Playwright |
| Dashboard | system/tasks/providers | visualizar estado | Playwright |
| Chat | conversations/providers | enviar y cancelar generación | Playwright |
| Modelos | providers/models | sincronizar modelos | Playwright |
| Agentes | agents/tools | crear y versionar agente | Playwright |
| Workflows | workflows | validar y ejecutar DAG | Playwright |
| Plugins | plugins | habilitar/deshabilitar | Playwright |
| Tareas | tasks | cancelar/reintentar | Playwright |
| Logs | observability | filtrar/correlacionar | Playwright |
| Configuración | configuration/security | guardar secreto | Playwright |

## Criterio de cierre

El Foundation Build solo está completo cuando:

1. Todos los requisitos obligatorios tienen implementación real.
2. Todas las pruebas mínimas están automatizadas o justificadas explícitamente.
3. Los criterios de aceptación de `03_SCOPE_AND_ACCEPTANCE.md` pasan.
4. No existen errores críticos o altos abiertos.
5. La instalación limpia funciona según `28_INSTALLATION_AND_OPERATIONS_CHECKLIST.md`.
6. El informe final incluye comandos ejecutados, resultados, limitaciones y deuda técnica aceptada.
