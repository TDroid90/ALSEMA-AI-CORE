# 14 — Frontend Architecture

## Propósito

Definir la arquitectura del frontend de ALSEMA AI CORE como una aplicación operativa, mantenible y desacoplada del backend.

El frontend no contiene reglas de negocio críticas. Consume contratos públicos de API, presenta estado, valida entradas y coordina experiencia de usuario.

## Stack

- React
- TypeScript estricto
- Vite
- React Router
- TanStack Query
- Zustand
- React Hook Form
- Zod
- Tailwind CSS
- Radix UI o primitives accesibles equivalentes
- Vitest
- React Testing Library
- Playwright

## Principios

1. Separar estado remoto de estado local.
2. No duplicar modelos del backend manualmente cuando puedan generarse desde OpenAPI.
3. Ningún componente debe ejecutar lógica de negocio compleja.
4. Toda operación asíncrona debe tener estados loading, empty, error y success.
5. Las acciones destructivas requieren confirmación explícita.
6. Las pantallas críticas deben tolerar reconexión y rehidratación.
7. La accesibilidad forma parte del criterio de aceptación.

## Estructura

```text
frontend/src/
  app/
    router/
    providers/
    layouts/
  features/
    auth/
    dashboard/
    chat/
    providers/
    models/
    agents/
    workflows/
    plugins/
    tasks/
    memory/
    logs/
    settings/
    users/
    system/
  shared/
    api/
    components/
    hooks/
    lib/
    schemas/
    stores/
    types/
    utils/
  styles/
  tests/
```

## Layout principal

- Sidebar colapsable.
- Header contextual.
- Área de contenido con ancho adaptable.
- Panel lateral opcional para detalles.
- Centro de notificaciones no intrusivo.
- Indicador persistente del estado del Core.

## Navegación v1

- Inicio
- Chat
- Proveedores
- Modelos
- Agentes
- Workflows
- Plugins
- Tareas
- Memoria
- Logs
- Usuarios
- Configuración
- Sistema

## Estado remoto

TanStack Query gestionará:

- cache;
- invalidación;
- reintentos limitados;
- deduplicación;
- polling cuando no exista canal push;
- sincronización tras mutaciones.

Las claves de consulta deben centralizarse por feature.

## Estado local

Zustand se limita a:

- preferencias de UI;
- paneles abiertos;
- borradores no persistidos;
- filtros temporales;
- selección de contexto.

No guardar en Zustand entidades remotas completas.

## API client

- Cliente HTTP único.
- Interceptores mínimos.
- Manejo centralizado de refresh token.
- Correlation ID por solicitud.
- Errores normalizados.
- Cancelación mediante AbortController.
- Tipos generados desde OpenAPI cuando sea viable.

## Tiempo real

Usar WebSocket o SSE según contrato backend.

Casos:

- streaming de chat;
- progreso de tareas;
- logs en vivo;
- cambios de estado de proveedores;
- actualizaciones de workflows.

Debe existir fallback a polling para progreso y estado.

## Chat

La interfaz debe soportar:

- streaming incremental;
- Markdown seguro;
- bloques de código;
- copiar contenido;
- detener generación;
- reintentar;
- editar y reenviar;
- selector de agente;
- selector de modelo o perfil;
- adjuntos permitidos;
- métricas básicas de ejecución;
- estados de error recuperables.

No renderizar HTML arbitrario del modelo.

## Formularios

- React Hook Form + Zod.
- Validación cliente alineada con servidor.
- Errores de campo y globales.
- Preservar datos cuando una petición falla.
- Confirmar navegación si existen cambios sin guardar.

## Tablas

Para modelos, tareas, logs y usuarios:

- paginación de servidor;
- filtros persistibles en URL;
- ordenamiento de servidor;
- columnas configurables cuando aporte valor;
- estados vacíos útiles;
- acciones por fila con permisos.

## Workflows

El editor visual v1 debe soportar:

- canvas con zoom y paneo;
- nodos arrastrables;
- conexiones tipadas;
- validación de grafo;
- panel de configuración;
- ejecución manual;
- visualización de estado por nodo;
- logs de ejecución.

No debe intentar replicar n8n completo.

## Accesibilidad

- Navegación por teclado.
- Foco visible.
- Contraste AA.
- Etiquetas accesibles.
- Modales con focus trap.
- Mensajes anunciables.
- No depender solo del color.

## Rendimiento

- Lazy loading por rutas.
- Virtualización en listas extensas.
- Evitar re-renderizados globales.
- Bundle analysis en CI cuando supere umbrales.
- Imágenes y assets optimizados.

## Seguridad frontend

- Nunca guardar secretos de proveedor.
- Access token en memoria cuando sea posible.
- Cookies seguras para refresh token si el backend adopta este patrón.
- Sanitización de Markdown.
- CSP compatible con la aplicación.
- Ocultar acciones sin permiso, sin asumir que eso reemplaza autorización backend.

## Criterios de aceptación

- Compilación TypeScript sin errores.
- Rutas protegidas operativas.
- Recuperación de sesión funcional.
- Chat con streaming funcional.
- Progreso de tareas en tiempo real o fallback.
- Formularios con validación y errores.
- Navegación accesible por teclado.
- Pruebas unitarias y E2E mínimas para flujos críticos.
