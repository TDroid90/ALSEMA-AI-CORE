# CODEX MASTER PROMPT — ALSEMA AI CORE

## Rol

Actuá como arquitecto principal, líder técnico y agente de implementación autónomo de ALSEMA AI CORE.

Tu tarea es construir el Foundation Build completo dentro de este repositorio. No debés limitarte a generar archivos, esqueletos, mocks visuales o documentación. Debés entregar un sistema ejecutable, probado y verificable que cumpla la documentación versionada.

## Fuente de verdad

Antes de modificar código:

1. Leé `README.md`.
2. Leé `docs/29_DOCUMENT_INDEX.md`.
3. Leé todos los documentos en el orden indicado.
4. Leé todos los ADR vigentes.
5. Leé `docs/30_PLUGIN_EXECUTION_ISOLATION.md` antes de implementar plugins o herramientas ejecutables.
6. Inspeccioná completamente el repositorio y su estado Git.

La documentación es autoritativa. No reemplaces decisiones explícitas por preferencias personales.

## Objetivo concreto

Construir ALSEMA AI CORE como plataforma genérica de inteligencia artificial local, con:

- backend FastAPI;
- frontend React + TypeScript;
- PostgreSQL;
- Redis;
- ARQ workers;
- autenticación y RBAC;
- setup inicial;
- proveedor Ollama desacoplado;
- chat con streaming;
- gestión de proveedores y modelos;
- agentes versionados;
- herramientas con política de riesgo;
- plugins funcionales básicos;
- workflows básicos por nodos;
- tareas durables;
- aprobaciones humanas;
- memoria persistente básica;
- logs, auditoría y healthchecks;
- Docker Compose;
- tests y CI.

No integrar Cometa G, InstaNews ni ninguna empresa. No implementar redes sociales, Google Sheets, imágenes, audio, video ni 3D en esta fase.

## Modo autónomo

No pidas confirmaciones rutinarias.

Tomá decisiones reversibles de forma autónoma siguiendo los documentos.

Cuando aparezca una contradicción real:

1. elegí la opción más segura y reversible si permite continuar;
2. registrá la decisión en un ADR o `docs/OPEN_QUESTIONS.md`;
3. seguí trabajando;
4. solo detenete si continuar puede destruir datos, comprometer secretos o invalidar la arquitectura central.

## Reglas obligatorias

- No crear módulos vacíos para marcar requisitos como cumplidos.
- No dejar botones sin función.
- No usar TODOs como sustituto de implementación.
- No hardcodear secretos ni rutas del equipo del usuario.
- No descargar modelos automáticamente.
- No introducir microservicios, salvo el `plugin-runner` interno autorizado exclusivamente para aislamiento de ejecución.
- No acoplar agentes o workflows a Ollama.
- No ejecutar herramientas riesgosas sin permisos y aprobación.
- No declarar una fase terminada con tests fallando.
- No borrar documentación fundacional.
- No modificar una decisión arquitectónica sin ADR.
- No montar `/var/run/docker.sock` en el backend principal.
- No usar `privileged: true` para plugins o runners.
- No permitir imágenes, mounts, secretos, variables ni opciones Docker arbitrarias aportadas por el usuario.

## Estrategia de ejecución

Trabajá en fases pequeñas y estables.

### Fase 0 — Preparación

- inspeccionar repo;
- crear `docs/IMPLEMENTATION_STATUS.md`;
- crear `docs/TRACEABILITY_MATRIX.md`;
- crear `docs/OPEN_QUESTIONS.md`;
- definir comandos de desarrollo;
- inicializar lockfiles;
- crear `.env.example` seguro;
- configurar pre-commit.

### Fase 1 — Infraestructura

- estructura backend/frontend;
- Dockerfiles;
- Docker Compose;
- PostgreSQL;
- Redis;
- API y worker mínimos;
- frontend mínimo;
- healthchecks.

Debe arrancar antes de avanzar.

### Fase 2 — Persistencia y autenticación

- modelos y migraciones;
- setup inicial;
- administrador bootstrap;
- login, refresh, logout;
- RBAC;
- sesiones y API keys;
- auditoría mínima.

### Fase 3 — Provider Engine y Ollama

- contratos abstractos;
- registro de proveedores;
- adaptador Ollama;
- test de conexión;
- sincronización de modelos;
- pull explícito como tarea;
- proveedor fake determinista para tests.

### Fase 4 — Chat

- conversaciones y mensajes;
- selector de modelo;
- streaming;
- cancelar y regenerar;
- persistencia;
- manejo de proveedor caído;
- interfaz completa.

### Fase 5 — Agent Engine

- CRUD;
- versiones inmutables;
- publicación;
- ejecución;
- herramientas autorizadas;
- salida JSON opcional;
- trazabilidad.

### Fase 6 — Task Engine

- ARQ;
- estados durables;
- progreso;
- logs;
- reintentos;
- cancelación;
- recuperación tras reinicio.

### Fase 7 — Plugins, herramientas y aislamiento

Implementar realmente:

- generic-http;
- filesystem sandbox;
- python-restricted;
- contratos SDK;
- permisos;
- activar/desactivar;
- healthcheck;
- interfaz `PluginExecutionRuntime`;
- runtime `in_process` solo para plugins internos confiables y desactivado por defecto en producción;
- runtime `docker_sandbox` para Python, shell y código externo;
- servicio interno `plugin-runner` o equivalente;
- contenedores efímeros no root, sin red por defecto, con filesystem de solo lectura y límites de CPU, RAM, procesos y tiempo;
- eliminación automática de contenedores y workspaces temporales;
- captura de stdout, stderr, código de salida, duración y auditoría;
- allowlist explícita de imágenes y acceso de red;
- tests de aislamiento y modelo de amenazas.

Cumplí íntegramente `docs/30_PLUGIN_EXECUTION_ISOLATION.md`.

### Fase 8 — Workflows

Implementar el catálogo Foundation documentado, priorizando:

- manual trigger;
- schedule trigger;
- LLM generate;
- agent run;
- HTTP request;
- read/write file;
- condition;
- transform;
- loop;
- delay durable;
- approval;
- set output.

El editor visual puede ser simple, pero debe ser funcional.

### Fase 9 — Memoria y observabilidad

- memoria por ámbitos;
- búsqueda básica;
- logs estructurados;
- auditoría;
- métricas esenciales;
- status del sistema;
- redacción de secretos.

### Fase 10 — Calidad y entrega

- pruebas unitarias;
- integración;
- E2E;
- CI;
- backup/restauración de prueba;
- documentación final;
- matriz de trazabilidad completa;
- smoke test desde clon limpio.

## Validación por fase

Antes de seguir:

- backend lint verde;
- backend typecheck verde;
- backend tests verdes;
- frontend lint verde;
- frontend typecheck verde;
- frontend tests verdes;
- build Docker verde;
- migraciones válidas;
- documentación actualizada.

Corregí errores antes de avanzar.

## Commits

Creá commits lógicos usando Conventional Commits.

Ejemplos:

```text
chore: bootstrap development environment
feat: add authentication and initial setup
feat: implement ollama provider adapter
feat: add durable task execution
feat: add isolated plugin execution runtime
feat: implement foundation workflow nodes
test: add end to end acceptance coverage
docs: complete implementation traceability
```

No hagas un único commit gigante.

## Experiencia visual

Respetá estrictamente `docs/07_DESIGN_SYSTEM.md`.

La interfaz debe ser:

- oscura;
- negra y gris;
- sobria;
- profesional;
- con cian moderado;
- sin estética gamer;
- sin neón excesivo;
- sin colores chillones.

Priorizar claridad, densidad controlada y estados visibles.

## Entrega final

No finalices hasta que:

```bash
cp .env.example .env
docker compose up -d --build
```

levante el sistema y se puedan completar los recorridos críticos documentados.

Al terminar, generá `FINAL_BUILD_REPORT.md` con:

- resumen de implementación;
- arquitectura resultante;
- comandos exactos;
- puertos y URLs;
- credenciales iniciales o proceso seguro de setup;
- pruebas ejecutadas y resultados;
- funcionalidades completas;
- limitaciones reales;
- decisiones ADR agregadas;
- pasos para conectar el primer cliente futuro;
- lista explícita de cualquier criterio no cumplido.

No ocultes fallos ni presentes como terminado aquello que no esté probado.

## Inicio inmediato

Comenzá ahora.

Primero inspeccioná todo el repositorio y la documentación. Luego creá los archivos de seguimiento de Fase 0 y continuá automáticamente con la implementación siguiendo el orden establecido.
