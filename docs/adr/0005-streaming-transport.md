# ADR-0005: Estrategia de transporte para streaming

- Estado: Aceptado
- Fecha: 2026-08-04

## Contexto

ALSEMA AI CORE necesita transmitir tokens de chat, progreso de tareas, logs y cambios de estado. No todas estas necesidades requieren comunicación bidireccional permanente.

WebSocket agrega complejidad operativa: reconexión, autenticación persistente, manejo de conexiones y escalabilidad. Server-Sent Events (SSE) ofrece un canal HTTP unidireccional más simple y suficiente para la mayoría de los streams del Foundation Build.

## Decisión

Usar **Server-Sent Events como transporte predeterminado** para:

- tokens de generación de chat;
- progreso de tareas;
- eventos de ejecución;
- logs en vivo filtrados.

Usar endpoints REST normales para comandos como enviar mensajes, cancelar tareas, aprobar operaciones y reintentar ejecuciones.

Reservar WebSocket para funcionalidades futuras que requieran comunicación bidireccional de baja latencia y justificar su incorporación mediante un ADR nuevo.

## Requisitos

- Cada evento SSE debe incluir tipo, timestamp, correlation ID y secuencia.
- El cliente debe poder reconectar usando `Last-Event-ID` cuando corresponda.
- Los eventos persistentes deben poder recuperarse mediante REST si el stream se interrumpe.
- No se enviarán secretos ni trazas internas sensibles.
- El servidor debe emitir heartbeat para detectar conexiones muertas.
- La cancelación se realiza mediante un comando REST idempotente, no escribiendo sobre el stream.

## Consecuencias

### Positivas

- Implementación y depuración más simples.
- Compatible con proxies HTTP comunes.
- Reconexión nativa del navegador.
- Separación clara entre comandos y eventos.

### Negativas

- Canal unidireccional.
- Límites de conexiones simultáneas según navegador/proxy.
- Algunas funcionalidades futuras podrían requerir WebSocket.

## Criterio de revisión

Revisar esta decisión cuando exista una necesidad real de colaboración simultánea, control interactivo continuo o comunicación binaria bidireccional.