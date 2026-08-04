# 28 — Checklist de Instalación y Operación

## Objetivo

Proporcionar una secuencia verificable para instalar, operar, diagnosticar, respaldar y actualizar ALSEMA AI CORE sin requerir conocimientos avanzados de desarrollo.

## Requisitos del host

- Windows 10/11 o Linux moderno.
- Docker Desktop o Docker Engine con Compose v2.
- Git.
- Ollama instalado en el host para el primer proveedor.
- Espacio libre suficiente para imágenes, base de datos, logs y modelos.
- GPU opcional pero recomendada; los modelos determinan requisitos reales.

## Instalación inicial

```bash
git clone https://github.com/TDroid90/ALSEMA-AI-CORE.git
cd ALSEMA-AI-CORE
cp .env.example .env
docker compose up -d --build
```

Después:

1. abrir la URL del frontend indicada en README;
2. completar setup inicial si corresponde;
3. iniciar sesión como administrador;
4. comprobar estado de PostgreSQL y Redis;
5. configurar URL de Ollama;
6. probar conexión;
7. sincronizar modelos instalados;
8. elegir un modelo por defecto;
9. ejecutar conversación de prueba.

## Variables mínimas

La implementación deberá documentar, al menos:

- entorno;
- puertos;
- URL pública;
- conexión PostgreSQL;
- conexión Redis;
- secreto JWT;
- clave maestra de cifrado;
- bootstrap admin o token de instalación;
- URL de Ollama;
- nivel de logs;
- directorios persistentes.

`.env.example` no contendrá valores secretos reales.

## Compatibilidad Ollama host → Docker

La detección debe contemplar:

- `host.docker.internal` en Docker Desktop;
- gateway configurable en Linux;
- URL manual;
- timeout configurable;
- mensaje diagnóstico claro cuando Ollama escucha solo en localhost o está bloqueado.

## Verificación rápida

Comandos esperados:

```bash
docker compose ps
docker compose logs --tail=200 api
docker compose logs --tail=200 worker
docker compose exec api alembic current
```

La interfaz deberá mostrar:

- versión del Core;
- estado API;
- estado base de datos;
- estado Redis;
- estado workers;
- estado Ollama;
- espacio disponible cuando sea posible;
- tareas activas.

## Inicio y detención

```bash
docker compose up -d
docker compose stop
docker compose down
```

`down` no debe borrar datos persistentes. La eliminación de volúmenes requiere un comando distinto y una advertencia explícita.

## Backups

El sistema deberá incluir scripts documentados para:

- dump de PostgreSQL;
- archivo de configuración no secreto;
- export de secretos cifrados cuando sea seguro;
- archivos y artefactos persistentes;
- manifest con versión del Core y fecha.

Ejemplo objetivo:

```bash
./scripts/backup.sh
```

En Windows debe existir alternativa PowerShell.

## Restauración

La restauración debe:

1. comprobar versión compatible;
2. detener escrituras;
3. validar el backup;
4. restaurar PostgreSQL;
5. restaurar storage;
6. ejecutar migraciones permitidas;
7. verificar readiness;
8. generar informe.

Debe existir una prueba automatizada de backup-restauración sobre datos de prueba.

## Actualización

Secuencia recomendada:

1. leer release notes;
2. crear backup;
3. descargar cambios o imágenes;
4. ejecutar comprobación previa;
5. aplicar migraciones;
6. levantar servicios;
7. ejecutar smoke tests;
8. conservar método de rollback.

## Diagnóstico

Problemas mínimos cubiertos por documentación:

- Ollama no accesible desde contenedor;
- modelo no instalado;
- memoria insuficiente;
- PostgreSQL no listo;
- Redis desconectado;
- worker detenido;
- migración pendiente;
- puerto ocupado;
- clave maestra incorrecta;
- descarga de modelo interrumpida;
- tarea trabada o huérfana.

## Retención

Configuración inicial recomendada:

- logs de aplicación rotativos;
- eventos de auditoría persistentes;
- outputs grandes mediante storage y referencias;
- limpieza de temporales programada;
- tareas completadas conservadas según política configurable.

## Recuperación después de reinicio

Al arrancar:

- detectar tareas en estado inconsistente;
- recuperar tareas reanudables;
- marcar fallos no recuperables con motivo;
- reprogramar delays y schedules;
- no duplicar ejecuciones;
- comprobar outbox pendiente.

## Checklist de entrega Foundation Build

- [ ] `docker compose up -d --build` funciona.
- [ ] Setup inicial funciona.
- [ ] Login funciona.
- [ ] Ollama puede configurarse y probarse.
- [ ] Modelos pueden sincronizarse.
- [ ] Chat con streaming funciona.
- [ ] Agente puede crearse, versionarse y ejecutarse.
- [ ] Workflow básico puede publicarse y ejecutarse.
- [ ] Tarea puede cancelarse y reintentarse.
- [ ] Approval puede aprobarse o rechazarse.
- [ ] Plugins funcionales se activan/desactivan.
- [ ] Logs y auditoría son consultables.
- [ ] Backup y restauración se verifican.
- [ ] Tests y CI pasan.
- [ ] No existen secretos ni credenciales de ejemplo inseguras.
