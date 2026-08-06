# ALSEMA AI CORE

> Núcleo local, extensible y autónomo de inteligencia artificial para el ecosistema ALSEMA.

## Estado

**Foundation Build v1.0 — implementación en curso.**

La especificación canónica sigue siendo la fuente de verdad. El corte funcional actual está documentado en `docs/IMPLEMENTATION_STATUS.md`.

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

La primera versión funcional debe entregar una base real y ejecutable con API REST versionada, streaming, autenticación, interfaz web oscura, chat con Ollama, proveedores abstractos, agentes, herramientas, plugins, workflows, tareas, logs, memoria, PostgreSQL, Redis, Docker Compose y pruebas automáticas.

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

## Arranque actual

1. Copiá `.env.example` a `.env`, reemplazá los valores de ejemplo y configurá un `APP_SECRET_KEY` único.
2. Configurá `INITIAL_ADMIN_EMAIL` e `INITIAL_ADMIN_PASSWORD` juntos, o dejá ambos vacíos para usar la pantalla inicial.
3. Ejecutá `docker compose up -d --build`.
4. Abrí `http://localhost:5173`; OpenAPI está en `http://localhost:8000/docs`.

PostgreSQL y Redis persisten en volúmenes Docker con nombre. Ollama queda externo y se conecta mediante `host.docker.internal`, de acuerdo con la arquitectura.

## Licencia

Pendiente de decisión. No asumir una licencia open source hasta que se documente formalmente.
