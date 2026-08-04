# ALSEMA AI CORE — MAKEBUILD v1.0

## 1. Rol de ejecución

A partir de este documento, Codex debe actuar como arquitecto principal, desarrollador senior y responsable de entrega del Foundation Build de ALSEMA AI CORE.

La tarea no consiste en producir snippets ni esqueletos. Consiste en construir una primera versión funcional, verificable y mantenible de la plataforma definida en este repositorio.

Codex debe trabajar de manera autónoma dentro del repositorio, sin detenerse a pedir confirmaciones sobre decisiones menores. Cuando exista una ambigüedad real, debe elegir la alternativa más conservadora, documentarla y continuar.

## 2. Orden obligatorio de lectura

Antes de modificar código o crear estructura, leer completamente:

1. `README.md`
2. `docs/00_MANIFESTO.md`
3. `docs/01_MAKEBUILD.md`
4. `docs/02_ARCHITECTURE.md`
5. `docs/03_SCOPE_AND_ACCEPTANCE.md`
6. todos los ADR aceptados en `docs/adr/`

Luego inspeccionar el árbol actual, historial reciente, archivos de configuración y estado de Git.

## 3. Reglas de autonomía

- No pedir confirmación para crear carpetas, dependencias, migraciones, pruebas o documentación previstas por esta especificación.
- No detenerse después de generar un plan. Ejecutar el plan.
- No declarar una fase terminada sin correr sus verificaciones.
- Ante un error, diagnosticarlo, corregirlo y volver a ejecutar la verificación.
- Si una dependencia propuesta ya no es apropiada, elegir una alternativa mantenida y registrar la decisión en un ADR.
- No descargar modelos de IA automáticamente.
- No borrar datos, ramas o archivos existentes sin una causa comprobada.
- No introducir servicios pagos ni credenciales externas obligatorias.

## 4. Estrategia de construcción

Usar un **monolito modular** para el backend, un frontend independiente y uno o más procesos worker. No dividir la aplicación en microservicios durante el Foundation Build.

Cada módulo debe poseer límites claros y exponer servicios de aplicación o contratos. La comunicación interna no debe depender de llamadas HTTP entre módulos del mismo backend.

## 5. Fases obligatorias

### Fase 0 — Inspección y diseño ejecutable

Entregables:

- inventario del repositorio;
- plan de trabajo en `docs/IMPLEMENTATION_PLAN.md`;
- registro de riesgos iniciales;
- ADRs para decisiones fundamentales aún no cubiertas;
- criterios de finalización por fase.

No crear arquitectura especulativa adicional. El plan debe mapearse a los criterios de aceptación.

### Fase 1 — Estructura y herramientas

Crear como mínimo:

```text
backend/
frontend/
docs/
docker/
scripts/
tests/
.env.example
docker-compose.yml
Makefile
pyproject.toml o backend/pyproject.toml
```

Configurar:

- formato, lint y tipado;
- pre-commit;
- variables de entorno tipadas;
- logging base;
- comandos reproducibles;
- GitHub Actions para backend y frontend.

Verificación:

- instalación reproducible;
- lint inicial limpio;
- pruebas mínimas ejecutables;
- configuración sin secretos reales.

### Fase 2 — Infraestructura local

Implementar Docker Compose con:

- API backend;
- frontend;
- PostgreSQL;
- Redis;
- worker ARQ;
- servicios auxiliares estrictamente necesarios.

Ollama debe considerarse un servicio externo configurable por URL, porque puede ejecutarse en el host Windows. Documentar el acceso desde Docker al host (`host.docker.internal`) y admitir una URL alternativa.

Agregar healthchecks reales y orden de arranque razonable.

### Fase 3 — Persistencia y migraciones

Crear SQLAlchemy 2 y Alembic.

Entidades mínimas:

- users;
- roles y permisos o un modelo RBAC equivalente;
- api_keys;
- providers;
- model_profiles;
- agents y agent_versions;
- conversations;
- messages;
- tools;
- workflows y workflow_versions;
- workflow_runs;
- tasks;
- task_events;
- memories;
- audit_events;
- system_settings.

Usar UUIDs, timestamps UTC, índices necesarios, restricciones explícitas y soft delete solo donde tenga una razón clara.

### Fase 4 — Instalación inicial y autenticación

Implementar:

- modo de primera instalación;
- administrador inicial desde variables de entorno o wizard seguro;
- login;
- access token corto;
- refresh token rotativo y revocable;
- cierre de sesión;
- recuperación administrativa documentada;
- RBAC básico;
- API keys con scopes y hash irreversible.

No guardar contraseñas ni tokens en texto plano.

### Fase 5 — Provider Engine y Ollama

Definir contratos independientes del proveedor para:

- listar modelos;
- comprobar salud;
- completar chat con streaming;
- completar texto sin streaming;
- salida estructurada cuando el proveedor lo permita;
- cancelación y timeout;
- métricas básicas de uso y latencia.

Implementar `OllamaProvider` como primer adaptador.

Debe:

- detectar disponibilidad;
- listar modelos locales;
- permitir solicitar descarga o eliminación solo mediante acción administrativa explícita;
- manejar errores de conexión y modelo ausente;
- no bloquear el event loop con operaciones síncronas.

### Fase 6 — Conversaciones y chat

Implementar de punta a punta:

- creación de conversación;
- mensajes de usuario y asistente;
- streaming;
- persistencia incremental segura;
- cancelación;
- regeneración;
- edición con bifurcación o semántica documentada;
- selector de agente y perfil de modelo;
- Markdown y bloques de código en el frontend.

Una interrupción del navegador no debe corromper el historial.

### Fase 7 — Agent Engine

Implementar agentes versionados con:

- nombre y descripción;
- system prompt;
- perfil de modelo;
- parámetros permitidos;
- herramientas asignadas;
- política de memoria;
- esquema de salida opcional;
- timeout;
- estado activo/inactivo.

Los cambios de configuración deben crear una nueva versión o quedar auditados de forma equivalente.

### Fase 8 — Tool y Plugin Engine básico

Implementar un registro de herramientas con contratos tipados.

Plugins funcionales mínimos:

- HTTP restringido y configurable;
- lectura/escritura de archivos dentro de un sandbox;
- ejecución Python controlada como tarea;
- utilidades internas seguras.

Cada herramienta debe declarar:

- identificador;
- descripción;
- esquema de entrada;
- esquema de salida;
- permisos requeridos;
- timeout;
- si produce efectos secundarios;
- política de auditoría.

No permitir shell arbitrario desde el chat en el Foundation Build.

### Fase 9 — Task Engine

Implementar tareas persistentes mediante ARQ y Redis.

Capacidades:

- crear;
- encolar;
- iniciar;
- actualizar progreso;
- finalizar;
- fallar;
- reintentar;
- cancelar de forma cooperativa;
- consultar historial y eventos.

Las tareas deben conservar resultado o referencia al resultado. Definir idempotency keys para endpoints adecuados.

### Fase 10 — Workflow Engine básico

Implementar definición versionada de workflow como grafo dirigido validado.

Nodos funcionales mínimos:

- input;
- LLM/agent;
- HTTP;
- archivo;
- Python controlado;
- condition;
- output.

El editor visual debe permitir crear, conectar, configurar, validar y ejecutar workflows básicos. No intentar reproducir n8n completo.

Cada ejecución debe transformarse en una tarea observable y registrar la salida de cada nodo con redacción de secretos.

### Fase 11 — Memoria básica

Implementar memoria persistente con ámbitos:

- global;
- usuario;
- proyecto/namespace de cliente;
- agente;
- conversación.

El Foundation Build puede usar búsqueda textual y metadatos. Vector store y embeddings son opcionales y solo se incorporarán mediante ADR si existe una implementación concreta, local y probada.

### Fase 12 — Dashboard y administración

Construir una interfaz utilizable con:

- inicio y estado general;
- chat;
- proveedores y modelos;
- agentes;
- herramientas/plugins;
- workflows;
- tareas;
- memoria;
- logs/auditoría;
- usuarios, roles y API keys;
- configuración del sistema.

No mostrar datos falsos. Si una métrica no está disponible, mostrar `No disponible` y explicar la causa.

### Fase 13 — Observabilidad y endurecimiento

Implementar:

- logs JSON en backend;
- correlation/request IDs;
- auditoría de acciones sensibles;
- métricas básicas de solicitudes, tareas y proveedor;
- redacción de secretos;
- límites de tamaño de archivos y payloads;
- rate limiting;
- CORS y headers seguros;
- manejo uniforme de errores.

### Fase 14 — Pruebas de aceptación y documentación

Ejecutar pruebas unitarias, integración y E2E.

Crear:

- guía de instalación en Windows con Docker Desktop y Ollama en host;
- guía operativa;
- referencia de variables de entorno;
- documentación de API;
- procedimiento de backup/restore;
- informe final en `docs/FOUNDATION_BUILD_REPORT.md`.

## 6. Convenciones técnicas

### Backend

- Python 3.12.
- Código asíncrono en bordes de I/O.
- Pydantic para contratos externos.
- Modelos ORM no expuestos directamente como respuestas API.
- Inyección de dependencias explícita.
- Excepciones de dominio traducidas en una sola capa.
- Fechas en UTC.
- Identificadores UUID.

### Frontend

- TypeScript estricto.
- Componentes accesibles.
- Estado del servidor en TanStack Query.
- Zustand solo para estado de interfaz o sesión cuando corresponda.
- Formularios con React Hook Form y Zod.
- No duplicar los contratos manualmente si puede generarse un cliente desde OpenAPI.

### API

- prefijo `/api/v1`;
- formato de error coherente;
- paginación estable;
- filtros documentados;
- idempotencia en operaciones largas o reintentables;
- nunca devolver secretos.

## 7. Manejo de errores durante la ejecución

Cuando una verificación falle:

1. conservar el mensaje completo;
2. identificar la causa raíz;
3. corregir la causa, no ocultar el síntoma;
4. agregar o ajustar una prueba que reproduzca el problema cuando sea razonable;
5. volver a ejecutar la verificación afectada;
6. ejecutar la suite de regresión relevante;
7. documentar la decisión si cambia arquitectura o comportamiento público.

No deshabilitar pruebas, tipado o lint para obtener un resultado verde.

## 8. Política de commits

Crear commits pequeños y coherentes al cerrar unidades verificadas.

Formato recomendado:

- `docs: ...`
- `chore: ...`
- `feat(auth): ...`
- `feat(providers): ...`
- `feat(agents): ...`
- `feat(workflows): ...`
- `fix(...): ...`
- `test(...): ...`

No hacer commits con una fase rota. No reescribir historia remota sin necesidad.

## 9. Prohibiciones

- No introducir lógica de empresas clientes.
- No crear endpoints ficticios que siempre devuelvan éxito.
- No usar mocks en producción.
- No incorporar secretos de desarrollo al repositorio.
- No ejecutar código arbitrario sin sandbox y autorización.
- No crear una dependencia circular entre módulos.
- No utilizar `TODO` como sustituto de un requisito obligatorio.
- No afirmar soporte para una función que no pase una prueba de aceptación.
- No implementar microservicios, Kubernetes o event streaming distribuido en esta etapa.

## 10. Entrega final obligatoria

Codex debe terminar dejando:

- repositorio limpio;
- servicios construibles;
- migraciones aplicables;
- pruebas verdes;
- documentación actualizada;
- `.env.example` completo;
- comandos de instalación y operación comprobados;
- informe de funciones terminadas, decisiones, riesgos y pendientes explícitos.

No debe cerrar la tarea con una lista de archivos generados. Debe demostrar que los flujos principales funcionan de punta a punta según `03_SCOPE_AND_ACCEPTANCE.md`.
