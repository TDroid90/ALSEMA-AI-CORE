# 15 — Ollama Provider

## Propósito

Definir la integración inicial con Ollama sin acoplar el dominio de ALSEMA AI CORE a su API específica.

Ollama será el primer proveedor operativo de texto y embeddings. No será una dependencia conceptual del Core.

## Responsabilidades del adaptador

- Detectar disponibilidad de Ollama.
- Consultar versión y estado.
- Listar modelos instalados.
- Consultar metadatos de modelo.
- Descargar modelos por acción explícita.
- Eliminar modelos con confirmación.
- Ejecutar chat con y sin streaming.
- Ejecutar generación de texto si se requiere.
- Generar embeddings cuando el modelo lo soporte.
- Traducir errores externos al catálogo interno.
- Emitir métricas y trazas.

## Contratos internos

El adaptador implementará capacidades separadas:

```python
class ChatProvider(Protocol): ...
class EmbeddingProvider(Protocol): ...
class ModelCatalogProvider(Protocol): ...
class ProviderHealthCheck(Protocol): ...
```

No crear una interfaz gigante que obligue a todos los proveedores a implementar capacidades inexistentes.

## Configuración

Variables mínimas:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_CONNECT_TIMEOUT_SECONDS=5
OLLAMA_READ_TIMEOUT_SECONDS=300
OLLAMA_HEALTHCHECK_INTERVAL_SECONDS=30
OLLAMA_MAX_CONCURRENT_REQUESTS=1
```

La concurrencia debe ser configurable por instalación y ajustada a la capacidad real de GPU y RAM.

## Descubrimiento

Al iniciar:

1. El Core arranca aunque Ollama no esté disponible.
2. Registra el proveedor como `unavailable`.
3. Ejecuta healthchecks periódicos con backoff.
4. Cuando Ollama aparece, sincroniza el catálogo local.
5. Nunca bloquea el arranque global por una dependencia de inferencia.

## Sincronización de modelos

La base del Core mantiene una representación propia de modelos.

La sincronización debe:

- crear o actualizar registros detectados;
- marcar como no disponibles los modelos retirados;
- conservar configuraciones y perfiles internos;
- no borrar historial;
- registrar fecha de última detección.

## Descarga de modelos

La descarga:

- solo puede iniciarla un usuario autorizado;
- muestra nombre, tamaño estimado si está disponible y advertencia;
- se ejecuta como tarea durable;
- emite progreso;
- admite cancelación cuando la API lo permita;
- no comienza automáticamente durante instalación o arranque.

## Streaming de chat

Flujo:

1. Validar proveedor, modelo, permisos y límites.
2. Crear ejecución interna.
3. Abrir streaming hacia Ollama.
4. Normalizar cada fragmento.
5. Persistir resultado final y métricas.
6. Emitir evento de cierre o error.

El cliente nunca recibe directamente el protocolo crudo de Ollama.

## Tool calling

El Core no debe asumir que todos los modelos de Ollama soportan tool calling de la misma forma.

Cada modelo tendrá capacidades detectadas o configuradas:

- chat;
- structured output;
- tools;
- embeddings;
- vision;
- context window aproximado.

Cuando una capacidad no esté verificada, debe tratarse como no disponible.

## Structured output

Para salidas JSON:

- usar formato nativo si existe;
- validar siempre contra esquema interno;
- intentar reparación controlada una cantidad limitada de veces;
- no aceptar JSON inválido silenciosamente;
- registrar intentos y motivo del fallo.

## Límites

- Semáforo de concurrencia por proveedor.
- Límite opcional por modelo.
- Cola para solicitudes no inmediatas.
- Timeout configurable.
- Cancelación cooperativa.
- Protección contra prompts y adjuntos excesivos.

## Errores normalizados

Ejemplos internos:

- `provider_unavailable`
- `model_not_found`
- `model_not_loaded`
- `unsupported_capability`
- `context_limit_exceeded`
- `provider_timeout`
- `provider_overloaded`
- `generation_cancelled`
- `invalid_provider_response`

No filtrar trazas internas al usuario final.

## GPU y telemetría

Ollama no será la única fuente para métricas de hardware. El módulo System podrá usar herramientas del sistema, por ejemplo NVIDIA SMI, cuando estén disponibles.

La UI debe distinguir:

- datos provistos por Ollama;
- datos detectados por el sistema;
- datos no disponibles.

## Compatibilidad Windows y Docker

El Foundation Build debe documentar y probar el escenario principal:

- Ollama instalado en Windows host.
- ALSEMA AI CORE ejecutándose con Docker Desktop.
- Acceso mediante `host.docker.internal`.

También debe admitir Ollama en otro host mediante URL configurable.

## Pruebas

- Unitarias con transporte HTTP simulado.
- Contrato contra respuestas representativas.
- Integración opcional marcada para requerir Ollama real.
- Prueba de proveedor caído.
- Prueba de streaming interrumpido.
- Prueba de sincronización de modelos.
- Prueba de JSON inválido.

## Criterios de aceptación

- El Core inicia sin Ollama.
- Detecta Ollama cuando está disponible.
- Lista modelos instalados.
- Ejecuta chat con streaming.
- Registra errores normalizados.
- Descarga un modelo solo tras acción explícita.
- No expone secretos ni protocolo crudo.
- Cambiar de adaptador no obliga a modificar agentes o workflows.
