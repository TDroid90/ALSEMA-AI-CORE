# 27 — CI/CD y Releases

## Objetivo

Definir una automatización mínima y obligatoria para garantizar que `main` permanezca estable y que cada versión pueda reproducirse.

## GitHub Actions

Workflows iniciales:

### `backend-ci.yml`

Se ejecuta en pull requests y pushes a `main` cuando cambia backend o configuración común.

Pasos:

1. checkout;
2. configurar Python 3.12;
3. instalar dependencias bloqueadas;
4. Ruff format check;
5. Ruff lint;
6. mypy;
7. pytest unit;
8. pytest integration con PostgreSQL y Redis de servicio;
9. verificar migraciones Alembic;
10. construir imagen backend.

### `frontend-ci.yml`

1. checkout;
2. configurar Node LTS fijado;
3. instalar con lockfile;
4. lint;
5. typecheck;
6. Vitest;
7. build de producción;
8. construir imagen frontend.

### `e2e.yml`

Se ejecuta en PRs relevantes y manualmente:

1. levantar stack efímero;
2. aplicar migraciones;
3. crear administrador de prueba;
4. usar proveedor fake determinista;
5. ejecutar Playwright;
6. guardar capturas y trazas al fallar;
7. destruir entorno.

### `security.yml`

- escaneo de secretos;
- auditoría de dependencias;
- análisis estático básico;
- generación de SBOM por release.

### `docker-compose-smoke.yml`

Valida que el comando documentado levante todos los servicios y que readiness responda correctamente.

## Protección de `main`

Recomendado:

- requerir CI verde;
- impedir force push;
- requerir rama actualizada para cambios de implementación;
- squash merge como opción preferida;
- no exigir PR para commits documentales hechos por el arquitecto mientras el repositorio está en Foundation, pero sí una vez iniciada la implementación.

## Versionado

SemVer:

- MAJOR: contratos incompatibles o migración mayor;
- MINOR: capacidades compatibles nuevas;
- PATCH: correcciones compatibles.

Antes de `1.0.0`, la versión del Foundation Build podrá evolucionar como `0.x`, pero los contratos publicados deben tratarse con disciplina.

## Releases

Cada release debe incluir:

- tag firmado o verificable;
- changelog;
- imágenes Docker etiquetadas;
- checksums cuando haya artefactos descargables;
- SBOM;
- notas de migración;
- backup recomendado antes de actualizar;
- lista de incompatibilidades conocidas.

## Estrategia de imágenes

Imágenes separadas:

- `alsema-ai-core-api`;
- `alsema-ai-core-worker`;
- `alsema-ai-core-web`.

API y worker podrán compartir base de imagen, pero tendrán comandos de ejecución distintos.

Etiquetas:

- versión exacta: `0.1.0`;
- minor flotante opcional: `0.1`;
- `latest` solo para releases estables;
- SHA corto para builds de CI.

## Migraciones en despliegue

- Nunca ejecutar migraciones destructivas automáticamente sin aviso.
- Proveer comando explícito de migración.
- Readiness falla si la base está en una versión incompatible.
- Documentar rollback cuando sea posible.
- Antes de una migración sensible, verificar backup.

## Entornos

### Desarrollo

- hot reload;
- logs legibles;
- volúmenes montados;
- proveedor fake opcional.

### Test

- datos efímeros;
- proveedor determinista;
- sin acceso externo por defecto.

### Producción local

- imágenes construidas;
- volúmenes persistentes;
- secretos fuera del repositorio;
- reinicio automático razonable;
- healthchecks activos.

## Dependabot o equivalente

- actualizaciones agrupadas y limitadas;
- no fusionar automáticamente cambios mayores;
- ejecutar suite completa;
- revisar cambios de licencias.

## Criterios de aceptación

- Un PR roto no puede considerarse listo.
- El stack se construye desde cero en CI.
- Las migraciones se prueban sobre base limpia.
- Los artefactos de fallos E2E son descargables.
- Una release puede instalarse siguiendo solo documentación versionada.
- La versión visible en frontend y API coincide con el tag.
