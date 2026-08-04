# Checklist final de revisión documental

## Objetivo

Validar que la Biblia estructural de ALSEMA AI CORE sea coherente, ejecutable por Codex y suficiente para iniciar la implementación sin decisiones críticas implícitas.

## Identidad y alcance

- [x] El Core está separado de Cometa G, InstaNews y demás clientes.
- [x] Ollama está definido como primer provider, no como dependencia del dominio.
- [x] El Foundation Build distingue implementación real de extensiones futuras.
- [x] Las funciones fuera de alcance están declaradas explícitamente.
- [x] No se promete replicar n8n, Open WebUI o un sistema operativo completo en la v1.

## Arquitectura

- [x] Está adoptado el monolito modular.
- [x] Existen límites entre dominio, aplicación, infraestructura y API.
- [x] Los módulos tienen responsabilidades y contratos definidos.
- [x] Los eventos internos usan outbox cuando requieren entrega durable.
- [x] Los providers están desacoplados por capacidades.
- [x] Las decisiones relevantes tienen ADR.

## Dominio y persistencia

- [x] Entidades, relaciones y estados principales están definidos.
- [x] PostgreSQL es la fuente durable de verdad.
- [x] Redis no almacena el único estado de una operación importante.
- [x] Existen migraciones, índices, auditoría y políticas de borrado.
- [x] Memoria y conversaciones están aisladas por scope/proyecto.

## Seguridad

- [x] Autenticación, sesiones, API keys, roles y permisos están especificados.
- [x] Los secrets se cifran y se redactan.
- [x] Las herramientas tienen nivel de riesgo y approvals.
- [x] Prompt injection no se considera un control de seguridad.
- [x] La ejecución de herramientas riesgosas usa sandbox.
- [x] El acceso a archivos y red está restringido.

## API y streaming

- [x] La API está versionada bajo `/api/v1`.
- [x] Hay formato uniforme de errores.
- [x] Se contempla idempotencia.
- [x] SSE es el transporte inicial de streaming.
- [x] Los comandos críticos usan REST y permisos explícitos.
- [x] OpenAPI forma parte del contrato verificable.

## Agentes, plugins y workflows

- [x] Los agentes son configuraciones versionadas.
- [x] Las herramientas están separadas del provider LLM.
- [x] Los plugins usan manifest y ciclo de vida.
- [x] Los plugins no dependen directamente entre sí.
- [x] Los workflows son DAGs validados.
- [x] Los nodos iniciales tienen contratos concretos.
- [x] Tareas, workflows y herramientas emiten progreso y auditoría.

## Frontend y diseño

- [x] La arquitectura frontend está definida.
- [x] La paleta oscura y el uso moderado del cian están fijados.
- [x] Las pantallas del Foundation Build están enumeradas.
- [x] Estados vacíos, carga, error y accesibilidad están contemplados.
- [x] La UI no oculta fallos de providers o workers.

## Operación

- [x] Docker Compose y `.env.example` están definidos como instalación principal.
- [x] Hay healthchecks y readiness.
- [x] Hay estrategia de logs, métricas y correlation IDs.
- [x] Backup y restauración están documentados.
- [x] Existe estrategia de actualización y rollback.
- [x] La descarga de modelos requiere acción explícita.

## Calidad

- [x] Están definidas pruebas unitarias, integración y E2E.
- [x] Existe matriz de trazabilidad requisito-prueba.
- [x] CI bloquea código que no cumple calidad mínima.
- [x] Codex debe ejecutar comandos y registrar resultados.
- [x] No se aceptan mocks permanentes, TODOs indefinidos ni rutas falsas.
- [x] Cada fase debe dejar el sistema ejecutable.

## Instrucción de cierre documental

La Biblia estructural está lista para implementación cuando este checklist no contiene bloqueos críticos y los documentos listados en `29_DOCUMENT_INDEX.md` existen en el repositorio.

Las correcciones menores descubiertas durante la implementación pueden documentarse mediante ADR o actualización del documento específico. Codex no debe rediseñar silenciosamente la arquitectura.
