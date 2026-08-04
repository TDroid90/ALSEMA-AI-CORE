# 29 — Índice Canónico de Documentación

## Orden obligatorio de lectura

1. `README.md`
2. `docs/00_MANIFESTO.md`
3. `docs/01_MAKEBUILD.md`
4. `docs/02_ARCHITECTURE.md`
5. `docs/03_SCOPE_AND_ACCEPTANCE.md`
6. `docs/04_DOMAIN_MODEL.md`
7. `docs/05_SECURITY_MODEL.md`
8. `docs/06_API_CONVENTIONS.md`
9. `docs/07_DESIGN_SYSTEM.md`
10. `docs/08_ROADMAP.md`
11. `docs/09_DATABASE.md`
12. `docs/10_BACKEND_STRUCTURE.md`
13. `docs/11_PLUGIN_SYSTEM.md`
14. `docs/12_AGENT_ENGINE.md`
15. `docs/13_WORKFLOW_AND_TASK_ENGINE.md`
16. `docs/14_FRONTEND_ARCHITECTURE.md`
17. `docs/15_OLLAMA_PROVIDER.md`
18. `docs/16_MEMORY_ENGINE.md`
19. `docs/17_OBSERVABILITY.md`
20. `docs/18_DEPLOYMENT.md`
21. `docs/19_TESTING_STRATEGY.md`
22. `docs/20_CODEX_EXECUTION_PLAN.md`
23. `docs/21_EVENT_SYSTEM.md`
24. `docs/22_CONFIGURATION_AND_SECRETS.md`
25. `docs/23_PLUGIN_CONTRACTS.md`
26. `docs/24_WORKFLOW_NODE_CATALOG.md`
27. `docs/25_OPENAPI_FOUNDATION.md`
28. `docs/26_CODE_STANDARDS.md`
29. `docs/27_CI_CD_AND_RELEASES.md`
30. `docs/28_INSTALLATION_AND_OPERATIONS_CHECKLIST.md`
31. `docs/adr/`

## Regla de precedencia

En caso de contradicción:

1. prevalece el criterio de aceptación específico;
2. luego el documento especializado más reciente;
3. luego un ADR aceptado más reciente;
4. luego arquitectura general;
5. finalmente manifiesto y README.

Codex debe detener una decisión irreversible cuando detecte contradicción real y registrar el conflicto en `docs/OPEN_QUESTIONS.md`. No debe inventar una salida silenciosa.

## Estado de madurez

- Fundamentos: cerrados.
- Arquitectura: cerrada para Foundation Build.
- Contratos de dominio: cerrados.
- Seguridad: cerrada para Foundation Build.
- API: superficie inicial cerrada.
- UI: dirección y arquitectura cerradas.
- Operación: cerrada.
- Implementación: pendiente de Codex.

## Documentos que la implementación deberá generar

Durante la construcción:

- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `docs/OPEN_QUESTIONS.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/TRACEABILITY_MATRIX.md`
- ADRs adicionales
- OpenAPI generado
- README de backend, frontend y plugins

## Trazabilidad

Cada fase del desarrollo debe enlazar:

- requisito;
- criterio de aceptación;
- módulo implementado;
- prueba automatizada;
- commit o PR.

La matriz final debe permitir verificar que ninguna función se declaró terminada sin evidencia.
