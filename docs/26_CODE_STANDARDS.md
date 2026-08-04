# 26 — Estándares de Código y Repositorio

## Objetivo

Establecer reglas obligatorias para que Codex y futuros colaboradores produzcan código coherente, revisable y mantenible.

## Principios

- Claridad antes que ingenio.
- Tipado antes que comentarios explicativos de errores evitables.
- Funciones pequeñas con una responsabilidad.
- Dependencias dirigidas hacia el dominio.
- Ningún módulo importa infraestructura concreta desde dominio.
- No introducir abstracciones sin uso real.
- No duplicar contratos.

## Python

- Python 3.12.
- Formato y lint con Ruff.
- Tipado estricto con mypy.
- Pydantic 2 para contratos externos y configuración.
- SQLAlchemy 2 con estilo tipado.
- `async` solo para operaciones realmente asíncronas.
- Excepciones de dominio específicas; no usar `Exception` como contrato.
- No usar diccionarios sin tipo cuando exista un esquema conocido.
- No realizar llamadas de red desde routers.
- No acceder directamente a sesiones SQLAlchemy desde endpoints.

### Convenciones

- módulos y funciones: `snake_case`;
- clases y protocolos: `PascalCase`;
- constantes: `UPPER_SNAKE_CASE`;
- IDs como tipos explícitos o UUID validados;
- enums persistidos con valores estables en minúsculas.

## TypeScript y React

- TypeScript estricto.
- No usar `any` salvo adaptación externa documentada.
- Componentes funcionales.
- TanStack Query para estado remoto.
- Zustand solo para estado cliente transversal.
- Zod para validación en límites.
- Formularios con React Hook Form.
- Componentes visuales sin lógica de infraestructura.
- Features agrupadas por dominio, no por tipo genérico de archivo.

## Errores

- Errores internos estructurados con código estable.
- Mensajes visibles comprensibles en español.
- Logs técnicos pueden estar en inglés si mejora interoperabilidad.
- Nunca revelar stack traces al cliente en producción.
- Cada request debe tener `request_id`.

## Logging

Logs estructurados JSON con, cuando aplique:

- timestamp;
- level;
- message;
- request_id;
- user_id;
- task_id;
- workflow_run_id;
- agent_id;
- plugin_id;
- provider_id.

No registrar prompts completos, tokens, contraseñas ni secretos sin una política explícita de redacción.

## Pruebas

- Cada caso de uso nuevo incluye pruebas.
- Corregir un bug exige prueba de regresión.
- Mockear límites externos, no el dominio completo.
- Las pruebas deben ser deterministas.
- No usar sleeps arbitrarios.
- E2E para recorridos críticos, no para cada detalle visual.

## Base de datos

- Toda modificación de esquema mediante Alembic.
- Migraciones revisables y con nombre descriptivo.
- Índices justificados por consultas reales.
- No almacenar JSON como sustituto de modelado sin justificarlo.
- Transacciones definidas en la capa de aplicación.

## Git

### Commits

Formato Conventional Commits:

```text
feat: add agent version publishing
fix: prevent duplicate scheduled runs
docs: define plugin lifecycle
refactor: isolate provider registry
test: cover refresh token rotation
chore: update development tooling
```

Cada commit debe:

- representar una unidad lógica;
- compilar;
- pasar pruebas relacionadas;
- no mezclar refactors masivos con funciones nuevas.

### Ramas

- `main`: siempre estable.
- ramas cortas: `feat/...`, `fix/...`, `docs/...`, `chore/...`.
- Pull Request para cambios de implementación importantes.

## Documentación

- ADR para decisiones arquitectónicas significativas.
- Docstrings para contratos públicos y comportamiento no evidente.
- README por plugin.
- OpenAPI como contrato vivo.
- CHANGELOG actualizado por versión, no por cada detalle menor.

## Dependencias

Antes de agregar una dependencia:

1. verificar si el stack ya resuelve el problema;
2. revisar mantenimiento y licencia;
3. justificar su función;
4. fijar rango de versión compatible;
5. agregar prueba mínima de integración cuando sea crítica.

## Prohibiciones

- Código comentado abandonado.
- TODOs sin issue o decisión asociada.
- Secretos en el repositorio.
- URLs y credenciales hardcodeadas.
- `eval` o ejecución de shell sin sandbox y permiso.
- Capturar excepciones y silenciarlas.
- Endpoints que devuelvan modelos ORM directamente.
- Migraciones automáticas destructivas al arrancar.
- Botones de interfaz sin funcionalidad real.

## Definición de terminado

Una unidad está terminada cuando:

- cumple el criterio de aceptación;
- tiene pruebas apropiadas;
- pasa lint, tipos y build;
- tiene manejo de errores;
- registra eventos y logs necesarios;
- respeta seguridad y permisos;
- actualiza documentación afectada;
- no deja placeholders ocultos.
