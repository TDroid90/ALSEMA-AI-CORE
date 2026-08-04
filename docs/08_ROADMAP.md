# 08 — Roadmap

## Propósito

Este roadmap organiza la construcción de ALSEMA AI CORE en etapas ejecutables. Cada etapa debe dejar el sistema en un estado coherente, probado y documentado. No se avanza si la etapa anterior no cumple sus criterios de aceptación.

## Regla de alcance

El Foundation Build no intenta resolver todos los casos futuros. Implementa completamente el núcleo necesario para operar con Ollama, agentes básicos, tareas, memoria persistente y workflows simples. Las integraciones empresariales se desarrollarán después como clientes o plugins.

# Fase 0 — Fundación documental

## Entregables

- README.
- Manifiesto.
- MAKEBUILD.
- Arquitectura.
- Alcance y aceptación.
- Modelo de dominio.
- Seguridad.
- Convenciones de API.
- Sistema visual.
- ADRs iniciales.

## Salida

Codex puede comprender el producto, el alcance y las restricciones sin depender del historial del chat.

# Fase 1 — Repositorio y calidad base

## Backend

- Proyecto Python 3.12.
- Gestión de dependencias reproducible.
- Ruff, mypy y pytest.
- Estructura de monolito modular.
- Configuración tipada.
- Logging estructurado.

## Frontend

- React + TypeScript + Vite.
- Tailwind y tokens del diseño.
- ESLint, TypeScript strict, Vitest.
- App shell inicial.

## Repositorio

- `.editorconfig`.
- `.gitignore`.
- `.env.example`.
- pre-commit.
- GitHub Actions.
- changelog.

## Aceptación

- Backend importa y testea.
- Frontend compila y testea.
- CI ejecuta ambos.

# Fase 2 — Infraestructura local

## Entregables

- Dockerfiles.
- Docker Compose.
- PostgreSQL.
- Redis.
- API.
- Worker ARQ.
- Frontend.
- Volúmenes persistentes.
- Healthchecks.

## Aceptación

`docker compose up -d --build` levanta todos los servicios obligatorios y `/health` responde correctamente.

# Fase 3 — Persistencia y bootstrap

## Entregables

- SQLAlchemy 2.
- Alembic.
- Repositorios base.
- Unit of Work.
- Migración inicial.
- Bootstrap idempotente.
- Administrador inicial.
- Estado de instalación.

## Aceptación

- Base vacía migra automáticamente.
- Reiniciar no duplica datos.
- Existe administrador funcional.

# Fase 4 — Identidad y acceso

## Entregables

- Login.
- Logout.
- Refresh rotation.
- Sesiones.
- RBAC.
- Usuarios y roles.
- API keys.
- Auditoría inicial.
- Rate limiting básico.

## Aceptación

- Accesos permitidos y denegados testeados.
- Revocación de sesión y API key efectiva.
- Secretos nunca aparecen en respuestas o logs.

# Fase 5 — Shell de producto

## Entregables

- Login visual.
- Sidebar.
- Header.
- Routing protegido.
- Dashboard de estado.
- Manejo global de errores.
- Loading y estados vacíos.
- Preferencias básicas.

## Aceptación

- Navegación funcional.
- Refresh conserva sesión.
- UI cumple los tokens definidos.

# Fase 6 — Provider Engine y Ollama

## Entregables

- Interfaz `LLMProvider`.
- Registro de proveedores.
- Adaptador Ollama.
- Healthcheck.
- Descubrimiento de modelos.
- Chat completion con streaming.
- Cancelación.
- Perfil de inferencia.
- Gestión visual de proveedor y modelos.

## Aceptación

- Detecta Ollama disponible/no disponible.
- Lista modelos instalados.
- Responde un chat real.
- Interrupción del streaming funciona.
- Ningún dominio depende directamente del SDK de Ollama.

# Fase 7 — Conversaciones

## Entregables

- CRUD de conversaciones.
- Mensajes persistentes.
- Historial.
- Títulos.
- Adjuntos básicos.
- Markdown y código.
- Métricas de inferencia.
- Ramas o regeneración sin alterar mensajes históricos.

## Aceptación

- Conversación sobrevive reinicios.
- Error de modelo queda representado.
- Streaming actualiza y finaliza correctamente.

# Fase 8 — Agent Engine

## Entregables

- Agentes.
- Versiones inmutables.
- Prompt del sistema.
- Perfil de inferencia.
- Tool policy.
- Memory policy.
- Esquema de salida opcional.
- Publicación y archivado.
- UI de edición y prueba.

## Aceptación

- Se crea y publica un agente.
- Conversación referencia versión concreta.
- Cambiar borrador no modifica ejecuciones pasadas.

# Fase 9 — Task Engine

## Entregables

- ARQ.
- Persistencia de tareas.
- Progreso.
- Reintentos con backoff.
- Cancelación cooperativa.
- Prioridades básicas.
- Eventos en tiempo real.
- UI de tareas.

## Aceptación

- Trabajo largo reporta progreso.
- Reintento no duplica efectos.
- Cancelación deja estado final coherente.

# Fase 10 — Tools y Plugin Engine básico

## Entregables

- Manifest de plugin.
- Registro.
- Estados y healthcheck.
- ToolDefinition.
- Validación JSON Schema.
- Clasificación de riesgo.
- Permisos.
- Plugin HTTP controlado.
- Plugin de archivos limitado al storage interno.
- Herramienta Python solo si existe sandbox seguro; de lo contrario queda fuera del Foundation Build.

## Aceptación

- Plugin inválido es rechazado.
- Herramienta sin permiso no ejecuta.
- Entradas y salidas quedan auditadas y redaccionadas.

# Fase 11 — Memoria básica

## Entregables

- MemoryEntry.
- Ámbitos.
- CRUD.
- Etiquetas.
- Búsqueda textual inicial.
- Políticas de expiración.
- Vinculación opcional a agentes.

## Aceptación

- No hay fuga entre ámbitos.
- Un agente puede recuperar memoria autorizada.
- Eliminación y expiración funcionan.

# Fase 12 — Workflow Engine básico

## Nodos funcionales iniciales

- Trigger manual.
- Input.
- LLM.
- HTTP.
- Transform.
- Condition.
- Delay corto o tarea diferida.
- Output.

## Entregables

- Definición de grafo.
- Validación.
- Versiones.
- Ejecución durable.
- Estado por nodo.
- Logs.
- Editor visual básico.

## Aceptación

Workflow mínimo ejecutable:

```text
Input → LLM → Output
```

Workflow con bifurcación:

```text
Input → Condition → HTTP/LLM → Output
```

# Fase 13 — Observabilidad y administración

## Entregables

- Logs estructurados consultables.
- Audit events.
- Métricas operativas.
- Estado de dependencias.
- Exportación básica.
- Correlation IDs.
- Modo mantenimiento.

## Aceptación

Un error de workflow puede rastrearse desde la ejecución hasta tarea, nodo, herramienta y proveedor.

# Fase 14 — Endurecimiento

## Entregables

- Pruebas de integración.
- Playwright.
- Límites y timeouts.
- Redacción de secretos.
- Pruebas de permisos.
- Manejo de fallos de PostgreSQL, Redis y Ollama.
- Backup/restore documentado.
- Revisión de dependencias.

## Aceptación

Se cumplen todos los casos de `03_SCOPE_AND_ACCEPTANCE.md`.

# Fase 15 — Entrega Foundation Build

## Entregables

- README operativo.
- Guía de instalación.
- Guía de actualización.
- OpenAPI.
- `.env.example` completo.
- Datos demo mínimos opcionales.
- Changelog.
- Tag `v0.1.0-foundation`.

## Estado esperado

ALSEMA AI CORE es operable localmente y está listo para recibir su primer cliente externo: Cometa G.

# Etapas posteriores

## v0.2 — Cometa G Client

Proyecto o plugin separado para:

- Google Sheets.
- Procesamiento por lotes.
- Reescritura de atributos.
- Descripción web.
- Descripción breve de WhatsApp.
- Copy para redes.
- Validación de resultados.

## v0.3 — InstaNews Client

- Ingesta de noticias.
- Reescritura neutral.
- Resúmenes.
- Flags de publicación.
- Preparación para TTS.

## v0.4 — Media Providers

- TTS.
- Imágenes mediante ComfyUI.
- Video.
- 3D mediante proveedores especializados.

Estas capacidades no se integran dentro del núcleo LLM; utilizan adaptadores de capacidades multimedia.

## v1.0 — Plataforma estable

- SDK oficial.
- API estable.
- Plugins firmados.
- Scheduler completo.
- Backups automatizados.
- Multiusuario maduro.
- Observabilidad ampliada.
- Migración y compatibilidad documentadas.
