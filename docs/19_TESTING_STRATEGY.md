# 19 — Testing Strategy

## Propósito

Definir una estrategia de pruebas suficiente para que cada fase del Foundation Build quede ejecutable y verificable, sin perseguir porcentajes artificiales de cobertura.

## Pirámide

### Unitarias

Validan dominio, servicios puros, políticas y transformaciones.

### Integración

Validan base de datos, Redis, adaptadores, migraciones y contratos entre módulos.

### Contrato

Validan proveedores, plugins, API y eventos públicos.

### End-to-end

Validan flujos críticos desde interfaz hasta persistencia y worker.

## Backend

Herramientas:

- pytest
- pytest-asyncio
- testcontainers cuando sea viable
- HTTPX TestClient/AsyncClient
- factories tipadas

Reglas:

- No compartir estado entre tests.
- Usar transacciones o bases aisladas.
- No depender de internet.
- Las pruebas con Ollama real son opcionales y etiquetadas.
- Congelar tiempo cuando corresponda.
- Probar permisos y errores, no solo caminos felices.

## Frontend

Herramientas:

- Vitest
- React Testing Library
- MSW
- Playwright

Prioridades:

- formularios;
- permisos visibles;
- estados de error;
- streaming;
- progreso de tareas;
- navegación;
- accesibilidad básica.

## Suites obligatorias

### Auth

- login válido e inválido;
- refresh;
- logout;
- sesión revocada;
- roles;
- API keys;
- rate limiting.

### Providers

- proveedor disponible y caído;
- modelo inexistente;
- timeout;
- streaming interrumpido;
- respuesta inválida;
- sincronización.

### Agents

- creación y versionado;
- ejecución sin herramientas;
- permisos de herramienta;
- structured output válido e inválido;
- cancelación;
- trazabilidad.

### Tasks

- encolado;
- progreso;
- reintento;
- cancelación;
- worker reiniciado;
- idempotencia;
- fallo terminal.

### Workflows

- grafo válido e inválido;
- dependencia entre nodos;
- retry por nodo;
- aprobación manual;
- reanudación;
- logs.

### Memory

- aislamiento;
- expiración;
- corrección;
- eliminación;
- inyección persistente;
- límites de contexto.

### Security

- acceso sin permiso;
- escalamiento horizontal;
- secretos en logs;
- payload excesivo;
- Markdown malicioso;
- path traversal;
- shell deshabilitado por defecto.

## E2E críticos

1. Primer inicio y login administrador.
2. Detectar Ollama.
3. Seleccionar modelo y conversar con streaming.
4. Crear agente y ejecutarlo.
5. Ejecutar tarea y observar progreso.
6. Crear workflow básico y ver resultado por nodo.
7. Reiniciar servicios y conservar datos.
8. Revocar API key y verificar rechazo.

## Smoke tests

Después de `docker compose up`:

- frontend responde;
- API liveness responde;
- API readiness responde;
- migración vigente;
- worker heartbeat;
- login;
- consulta de proveedores;
- creación de conversación.

## Cobertura

No fijar 100% como objetivo.

Umbrales iniciales sugeridos:

- dominio y seguridad: 90%;
- servicios de aplicación: 80%;
- adaptadores: 70%;
- frontend crítico: cobertura basada en flujos.

Una línea cubierta sin aserción útil no aporta calidad.

## CI

Cada push debe ejecutar:

- formato y lint;
- type checking;
- unitarias;
- integración compatible con CI;
- build backend y frontend;
- análisis de migraciones;
- escaneo básico de secretos y dependencias.

E2E puede ejecutarse en PR o rama principal según costo.

## Datos de prueba

- Sin datos reales de empresas.
- Fixtures pequeñas y legibles.
- Secrets ficticios.
- Prompts de prueba sin información sensible.

## Criterios de aceptación

- Ninguna fase se declara terminada con tests fallando.
- Los flujos críticos tienen E2E.
- Las migraciones se prueban sobre base limpia.
- Los fallos de proveedor no tumban toda la suite.
- Seguridad y aislamiento tienen pruebas negativas.
- Existe un comando documentado para ejecutar todas las suites.
