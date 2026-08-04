# 18 — Deployment

## Propósito

Definir un despliegue local reproducible, seguro y comprensible para una persona no desarrolladora, manteniendo una arquitectura que pueda evolucionar.

## Escenario principal v1

- Windows 11 como host.
- Docker Desktop.
- Ollama instalado en el host.
- ALSEMA AI CORE en contenedores.
- NVIDIA GPU disponible para Ollama.
- Acceso local mediante navegador.

## Servicios Docker Compose

- `frontend`
- `api`
- `worker`
- `postgres`
- `redis`

Servicios opcionales futuros no deben agregarse hasta tener uso real.

## Ollama

Por defecto:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

Debe poder cambiarse por URL sin reconstruir imágenes.

## Primer inicio

Flujo esperado:

```bash
cp .env.example .env
docker compose up -d --build
```

Luego:

1. Esperar healthchecks.
2. Aplicar migraciones automáticamente mediante un proceso controlado.
3. Crear administrador inicial desde variables de entorno si no existe.
4. Abrir la interfaz web.
5. Mostrar asistente inicial.
6. Detectar Ollama.
7. Permitir seleccionar o descargar modelo explícitamente.

## Variables obligatorias

- `APP_ENV`
- `APP_SECRET_KEY`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `REDIS_URL`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `OLLAMA_BASE_URL`

`.env.example` debe documentar cada valor sin incluir secretos reales.

## Persistencia

Volúmenes separados para:

- PostgreSQL;
- archivos de aplicación;
- logs locales cuando correspondan;
- backups.

Los modelos de Ollama permanecen fuera del Core si Ollama corre en el host.

## Healthchecks

Docker Compose debe definir healthchecks para:

- PostgreSQL;
- Redis;
- API;
- worker;
- frontend cuando sea viable.

La dependencia de arranque no reemplaza reintentos en aplicación.

## Migraciones

- Alembic como única fuente de cambios de esquema.
- No ejecutar `create_all` en producción.
- Migraciones reversibles cuando sea razonable.
- Backup antes de migraciones destructivas.
- Registro de versión aplicada.

## Backups

v1 debe incluir scripts documentados para:

- backup de PostgreSQL;
- restauración;
- exportación de configuración no secreta;
- verificación básica del archivo generado.

No declarar backup exitoso sin validar el resultado.

## Actualización

Flujo documentado:

1. Backup.
2. Obtener nueva versión.
3. Leer notas de versión.
4. Reconstruir contenedores.
5. Aplicar migraciones.
6. Verificar healthchecks.
7. Ejecutar smoke tests.
8. Conservar estrategia de rollback.

## Seguridad de red

- PostgreSQL y Redis no se publican fuera de la red Docker por defecto.
- Solo frontend y API publican puertos necesarios.
- CORS limitado.
- Bind local por defecto.
- Exposición LAN requiere configuración explícita.
- TLS queda preparado para reverse proxy futuro.

## Modos

### Development

- hot reload;
- logs detallados;
- puertos de desarrollo;
- datos no productivos.

### Production local

- imágenes optimizadas;
- sin hot reload;
- logs estructurados;
- secretos obligatorios;
- configuración endurecida.

## Scripts operativos

Crear scripts simples y documentados:

- `scripts/start.ps1`
- `scripts/stop.ps1`
- `scripts/status.ps1`
- `scripts/logs.ps1`
- `scripts/backup.ps1`
- `scripts/restore.ps1`
- equivalentes shell cuando sea útil.

## Criterios de aceptación

- Una instalación limpia levanta con Docker Compose.
- Ollama del host es detectable.
- Reiniciar contenedores no pierde datos.
- PostgreSQL y Redis no quedan expuestos públicamente.
- Existe backup y restauración probados.
- El administrador inicial se crea una sola vez.
- La UI informa dependencias degradadas.
