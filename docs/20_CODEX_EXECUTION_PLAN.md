# 20 — Codex Autonomous Execution Plan

## Rol

Codex actuará como arquitecto de implementación y desarrollador principal de ALSEMA AI CORE.

Su función es convertir la documentación versionada en una aplicación funcional, verificable y mantenible.

No debe reinterpretar la identidad del producto ni ampliar el alcance por iniciativa propia.

## Orden de lectura obligatorio

Antes de modificar el repositorio debe leer completamente:

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
11. Documentos `09` a `19`
12. Todos los ADR aceptados

## Regla de ejecución

No limitarse a producir propuestas. Crear archivos, instalar dependencias, ejecutar comandos, corregir errores y verificar resultados.

No pedir confirmación entre fases salvo que exista un bloqueo externo real que no pueda resolverse de forma segura.

## Inspección inicial

1. Verificar estado Git.
2. Listar estructura.
3. Leer documentación.
4. Detectar archivos existentes.
5. Verificar Docker, Python y Node disponibles.
6. Registrar restricciones del entorno.
7. Crear `docs/IMPLEMENTATION_STATUS.md`.
8. Crear checklist por fase con estado verificable.

## Fases de implementación

### Fase 1 — Tooling y estructura

Crear:

- `backend/`
- `frontend/`
- `docker/`
- `scripts/`
- `tests/`
- `.github/workflows/`
- `.env.example`
- `docker-compose.yml`
- configuración de lint, tipos y tests.

Criterio de salida:

- proyectos backend y frontend inicializan;
- lint básico ejecuta;
- Docker Compose valida;
- documentación de arranque actualizada.

### Fase 2 — Infraestructura backend

Implementar:

- FastAPI;
- configuración tipada;
- logging estructurado;
- correlation ID;
- manejo uniforme de errores;
- SQLAlchemy async;
- Alembic;
- Redis;
- ARQ;
- healthchecks.

Criterio de salida:

- API arranca;
- PostgreSQL y Redis conectan;
- migración inicial aplica;
- worker reporta heartbeat;
- pruebas de infraestructura pasan.

### Fase 3 — Autenticación y autorización

Implementar:

- usuario administrador inicial;
- login;
- access y refresh tokens;
- revocación;
- RBAC;
- API keys;
- auditoría;
- rate limiting básico.

Criterio de salida:

- flujo login-refresh-logout probado;
- rutas protegidas;
- API key revocable;
- permisos negativos probados.

### Fase 4 — Provider Engine y Ollama

Implementar contratos de proveedor y adaptador Ollama:

- healthcheck;
- catálogo de modelos;
- sincronización;
- chat;
- streaming;
- embeddings si disponible;
- descarga explícita como tarea;
- errores normalizados.

Criterio de salida:

- Core arranca sin Ollama;
- detecta Ollama disponible;
- lista modelos;
- conversa con streaming usando un modelo instalado;
- tests simulados pasan.

### Fase 5 — Conversaciones y chat

Implementar:

- conversaciones;
- mensajes;
- persistencia;
- streaming;
- detener generación;
- reintentar;
- métricas básicas;
- adjuntos solo en formatos inicialmente permitidos.

Criterio de salida:

- conversación completa desde UI;
- historial persiste;
- errores recuperables;
- sanitización de Markdown.

### Fase 6 — Agent Engine

Implementar:

- CRUD;
- versiones inmutables;
- configuración de modelo;
- permisos de herramientas;
- structured output;
- ejecuciones auditables;
- cancelación.

Criterio de salida:

- crear, versionar y ejecutar agente;
- salida JSON validada;
- permisos denegados correctamente.

### Fase 7 — Task Engine

Implementar:

- estados;
- progreso;
- logs;
- reintentos;
- cancelación;
- reconciliación tras reinicio;
- idempotencia.

Criterio de salida:

- tarea durable observable desde UI;
- reinicio de worker no pierde estado;
- reintento controlado.

### Fase 8 — Plugin y Tool Engine

Implementar:

- manifiesto;
- registro;
- activación;
- permisos;
- healthcheck;
- plugin HTTP seguro;
- plugin de archivos restringido;
- Python sandbox limitado o deshabilitado por defecto si no puede asegurarse.

Criterio de salida:

- plugins demostrativos funcionales;
- aislamiento de rutas;
- auditoría;
- acciones riesgosas requieren aprobación.

### Fase 9 — Workflow Engine básico

Implementar nodos:

- input;
- transform;
- LLM;
- condition;
- HTTP;
- file;
- output;
- approval.

Implementar:

- editor visual básico;
- validación de grafo;
- ejecución por nodos;
- estado y logs por nodo;
- reanudación.

Criterio de salida:

- workflow funcional de extremo a extremo;
- fallo y reintento visibles;
- aprobación manual operativa.

### Fase 10 — Memory Engine

Implementar:

- CRUD;
- ámbitos;
- búsqueda básica;
- TTL;
- contexto inyectado trazable;
- compactación conversacional inicial.

Criterio de salida:

- aislamiento probado;
- memoria inspeccionable;
- eliminación y expiración funcionales.

### Fase 11 — Dashboard y sistema

Implementar:

- estado general;
- salud de componentes;
- métricas básicas;
- GPU/VRAM si están disponibles;
- logs;
- tareas;
- configuración;
- usuarios.

Criterio de salida:

- dashboard refleja estado real;
- no inventa métricas ausentes;
- filtros y detalles operativos.

### Fase 12 — Endurecimiento y entrega

- completar pruebas;
- E2E críticos;
- backups y restore;
- scripts PowerShell;
- CI;
- revisión de secretos;
- documentación final;
- smoke test limpio.

Criterio de salida:

- todos los criterios de `03_SCOPE_AND_ACCEPTANCE.md` satisfechos;
- instalación limpia documentada;
- ninguna prueba obligatoria falla.

## Comandos obligatorios

Codex debe descubrir y documentar comandos concretos. Como mínimo debe existir una experiencia equivalente a:

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=200
```

Backend:

```bash
ruff check .
ruff format --check .
mypy .
pytest
```

Frontend:

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

E2E:

```bash
npm run test:e2e
```

## Manejo de errores

Ante un error:

1. Reproducirlo.
2. Capturar salida relevante.
3. Identificar causa raíz.
4. Corregir la causa, no ocultar el síntoma.
5. Agregar o ajustar prueba.
6. Reejecutar la suite afectada.
7. Documentar la decisión si modifica arquitectura.

No desactivar tests, linters o tipos para obtener una falsa finalización.

## Commits

Cada commit debe:

- representar un estado coherente;
- tener mensaje descriptivo;
- no mezclar cambios no relacionados;
- incluir documentación y tests correspondientes.

Ejemplos:

- `build: initialize backend and frontend workspaces`
- `feat(auth): implement refresh token rotation`
- `feat(providers): add Ollama streaming adapter`
- `test(tasks): cover worker recovery and retries`

## Informe de progreso

Actualizar `docs/IMPLEMENTATION_STATUS.md` después de cada fase con:

- estado;
- funcionalidades completadas;
- pruebas ejecutadas;
- comandos usados;
- bloqueos;
- deuda aceptada explícitamente;
- siguiente fase.

## Prohibiciones

- No implementar clientes empresariales.
- No integrar redes sociales.
- No agregar generación de imágenes, audio, video o 3D.
- No descargar modelos automáticamente.
- No usar datos reales.
- No exponer PostgreSQL o Redis públicamente.
- No guardar secretos en Git.
- No inventar tests pasados.
- No declarar producción lista si faltan criterios.
- No crear microservicios sin ADR aprobado.

## Definición de terminado

La construcción inicial termina únicamente cuando:

- Docker Compose levanta una instalación limpia;
- login funciona;
- Ollama se detecta;
- chat con streaming funciona;
- agente funciona;
- tarea durable funciona;
- plugin básico funciona;
- workflow básico funciona;
- memoria básica funciona;
- dashboard y logs funcionan;
- pruebas obligatorias pasan;
- documentación refleja el sistema real.

## Informe final

Codex debe entregar en el repositorio un `FINAL_BUILD_REPORT.md` con:

- resumen de lo construido;
- arquitectura final;
- instrucciones exactas de instalación;
- credenciales iniciales y cómo cambiarlas, sin publicar secretos reales;
- servicios y puertos;
- pruebas ejecutadas y resultados;
- limitaciones conocidas;
- decisiones ADR;
- pasos para conectar el primer cliente externo.
