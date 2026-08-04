# ADR 0002 — Abstracción de proveedores con Ollama como primer adaptador

- Estado: Aceptado
- Fecha: 2026-08-03

## Contexto

El primer uso del Core será local y utilizará Ollama. Sin embargo, el producto debe poder incorporar LM Studio, servidores compatibles con OpenAI, vLLM y proveedores cloud sin reescribir agentes, conversaciones, workflows o clientes.

Las APIs de cada proveedor difieren en streaming, tool calling, modelos, métricas, embeddings y errores.

## Decisión

Definir contratos internos por capacidad, no una interfaz gigante específica de un proveedor.

Contratos iniciales:

- `ChatCompletionProvider`
- `ModelCatalogProvider`
- `HealthCheckProvider`
- `EmbeddingProvider` cuando se implemente embeddings

El adaptador Ollama traducirá sus respuestas y errores al modelo canónico del Core.

Los agentes y workflows dependerán de servicios de aplicación que seleccionan un proveedor por configuración y capacidad. No importarán clientes, schemas ni excepciones de Ollama.

## Modelo canónico mínimo

La respuesta normalizada debe contemplar:

- contenido y deltas de streaming;
- finish reason;
- uso de tokens cuando esté disponible;
- latencia;
- tool calls normalizadas;
- identificador de proveedor y modelo;
- error tipado;
- metadatos no portables dentro de un campo separado.

## Consecuencias positivas

- Cambio de proveedor sin modificar dominio.
- Pruebas con proveedores falsos.
- Selección futura por capacidad, costo o disponibilidad.
- Errores consistentes para la UI y clientes.

## Riesgos

- El modelo común puede ocultar capacidades únicas.
- Intentar una abstracción perfecta demasiado pronto.

## Mitigaciones

- Contratos pequeños por capacidad.
- Campo de metadata específica no usado por el dominio.
- Ampliar interfaces solo cuando exista una segunda implementación o necesidad comprobada.
- No simular capacidades que Ollama o el modelo no soporten.

## Restricciones

- El Core no descargará modelos automáticamente durante bootstrap.
- La descarga o eliminación de modelos requiere acción administrativa explícita.
- La indisponibilidad de Ollama degrada funciones de IA, pero no debe impedir abrir el dashboard ni administrar la plataforma.
