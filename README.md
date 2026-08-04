# ALSEMA AI CORE

> Núcleo local, extensible y autónomo de inteligencia artificial para el ecosistema ALSEMA.

## Estado

**Foundation Build v1.0 — Biblia estructural cerrada y lista para implementación con Codex.**

La arquitectura, los contratos, la seguridad, el alcance, el diseño, la operación y los criterios de aceptación ya están documentados. La implementación del servidor todavía no comenzó.

Este repositorio es la única fuente de verdad de ALSEMA AI CORE. Contendrá la documentación fundacional, la arquitectura, el backend, el frontend, los proveedores de IA, los agentes, las herramientas, los plugins, los workflows, la memoria, la seguridad, las pruebas y el despliegue.

## Qué es

ALSEMA AI CORE es una plataforma local de inteligencia artificial diseñada para operar como infraestructura central de múltiples aplicaciones y empresas.

El Core no contiene lógica propia de Cometa G, InstaNews, CreativoSur, CanastApp, Peak, MascotApps ni de ninguna otra unidad de negocio. Esas soluciones serán clientes externos que consumirán las APIs, SDKs, eventos y plugins publicados por esta plataforma.

El proveedor inicial de modelos será Ollama. La arquitectura admite otros proveedores mediante adaptadores, sin modificar agentes, workflows ni clientes.

## Qué no es

- No es un chatbot aislado.
- No es un wrapper visual de Ollama.
- No es una copia de Open WebUI, n8n o Flowise.
- No es un proyecto de demostración.
- No es una aplicación específica de ninguna empresa.
- No debe acoplarse a un proveedor, modelo o sistema operativo concreto.

## Objetivo del Foundation Build

La primera versión funcional debe entregar una base real y ejecutable con:

- API REST versionada.
- Streaming mediante Server-Sent Events.
- Autenticación y administración inicial.
- Interfaz web oscura, sobria y profesional.
- Chat operativo mediante Ollama.
- Abstracción de proveedores de IA.
- Gestión de modelos y configuraciones.
- Motor de agentes reutilizables.
- Motor básico de herramientas y plugins.
- Motor básico de workflows por nodos.
- Cola de tareas, reintentos, progreso y cancelación.
- Logs estructurados y estado del sistema.
- Memoria persistente básica con separación por ámbito.
- PostgreSQL, Redis y migraciones.
- Docker Compose para desarrollo y operación local.
- Pruebas automáticas y documentación OpenAPI.

Las integraciones empresariales, redes sociales, Google Sheets, generación de audio, imágenes, video y 3D quedan fuera de esta primera implementación. Están previstas mediante contratos extensibles, pero no deben simularse con código superficial.

## Principios

1. **Core primero:** las empresas son clientes, nunca módulos internos.
2. **Contratos antes que implementaciones:** las capacidades se publican mediante interfaces estables.
3. **Local por defecto:** la plataforma debe funcionar sin servicios de IA pagos.
4. **Proveedor intercambiable:** Ollama es el primer adaptador, no el dominio.
5. **Seguridad explícita:** ningún agente ejecuta herramientas sin permisos definidos.
6. **Observabilidad:** toda tarea importante debe poder rastrearse.
7. **Recuperación:** los trabajos largos deben reanudarse o reintentarse sin perder estado.
8. **Evolución incremental:** cada fase debe dejar el sistema ejecutable.
9. **Nada de arquitectura vacía:** una interfaz existe solo cuando tiene un uso concreto o una extensión documentada.
10. **Documentación como código:** las decisiones relevantes viven versionadas en este repositorio.

## Diseño visual

- Fondo principal: `#0B0B0B`
- Superficies: `#141414`
- Superficie elevada: `#1A1A1A`
- Bordes: `#292929`
- Texto principal: `#F2F2F2`
- Texto secundario: `#A0A0A0`
- Acento cian: `#00B8D9`

El cian se utilizará con moderación para estados activos, foco, enlaces y métricas relevantes. No se utilizarán degradados chillones, estética gamer ni neón excesivo.

## Entrada para Codex

Abrir el repositorio en Codex y utilizar:

```text
Lee CODEX_MASTER_PROMPT.md y ejecutalo íntegramente. Antes de implementar, lee la documentación en el orden definido por docs/29_DOCUMENT_INDEX.md. Trabaja de forma autónoma por fases, ejecuta pruebas y no declares una fase terminada sin evidencia.
```

El archivo `CODEX_MASTER_PROMPT.md` es la instrucción ejecutiva. La carpeta `docs/` es la especificación autoritativa.

## Orden mínimo de lectura

1. `README.md`
2. `CODEX_MASTER_PROMPT.md`
3. `docs/29_DOCUMENT_INDEX.md`
4. `docs/00_MANIFESTO.md`
5. `docs/01_MAKEBUILD.md`
6. `docs/02_ARCHITECTURE.md`
7. `docs/03_SCOPE_AND_ACCEPTANCE.md`
8. ADRs aceptados

En caso de contradicción, aplicar la precedencia definida en `docs/29_DOCUMENT_INDEX.md`.

## Stack objetivo inicial

### Backend

- Python 3.12
- FastAPI
- Pydantic 2
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Redis
- ARQ
- HTTPX
- JWT con rotación de refresh tokens
- Server-Sent Events

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query
- Zustand
- React Hook Form
- Zod

### Calidad

- Ruff
- mypy
- pytest
- Vitest
- Playwright
- pre-commit
- GitHub Actions

## Arranque esperado al finalizar la implementación

```bash
cp .env.example .env
docker compose up -d --build
```

La plataforma deberá exponer frontend, API, documentación OpenAPI, PostgreSQL, Redis, worker de tareas y estado de conexión con Ollama.

La descarga de modelos será una acción explícita del administrador. El sistema no descargará modelos de gran tamaño sin autorización.

## Licencia

Pendiente de decisión. No asumir una licencia open source hasta que se documente formalmente.
