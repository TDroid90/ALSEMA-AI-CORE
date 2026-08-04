# Glosario canónico — ALSEMA AI CORE

Este glosario fija el significado de los términos utilizados en la documentación y el código. Codex no debe introducir sinónimos innecesarios para conceptos ya definidos.

## Core

La plataforma central ALSEMA AI CORE. No contiene lógica específica de empresas clientes.

## Cliente

Aplicación externa que consume las capacidades del Core mediante API, SDK, eventos o plugins autorizados. Cometa G e InstaNews serán clientes futuros.

## Provider

Adaptador que ofrece una capacidad de inteligencia artificial o cómputo externo. Ejemplo inicial: Ollama como proveedor LLM.

## Modelo

Recurso ejecutable publicado por un provider. Un modelo no es un agente y no contiene permisos de herramientas.

## Perfil de inferencia

Configuración reutilizable de parámetros para ejecutar un modelo: temperatura, top-p, contexto, límites y formato de salida.

## Agente

Configuración versionada que combina instrucciones, provider/modelo, perfil de inferencia, memoria y herramientas autorizadas para cumplir una función.

## Herramienta

Capacidad invocable por un agente o workflow mediante contrato tipado. Toda herramienta tiene nivel de riesgo, permisos y auditoría.

## Plugin

Paquete extensible con manifest y ciclo de vida que registra herramientas, nodos, proveedores u otras extensiones permitidas. Los plugins no deben depender directamente entre sí.

## Workflow

Definición versionada de un grafo dirigido de nodos y conexiones que procesa una entrada hasta producir una salida.

## Nodo

Unidad ejecutable dentro de un workflow. Declara entradas, salidas, configuración, timeout y política de error.

## Tarea

Unidad durable de trabajo en segundo plano. Tiene identidad, estado, progreso, logs, reintentos y cancelación.

## Ejecución

Instancia concreta de un agente, herramienta, workflow o tarea. Conserva datos de entrada, salida, duración y errores según políticas de retención.

## Conversación

Contenedor persistente de mensajes entre usuario y asistente, separado por proyecto y permisos.

## Mensaje

Elemento de una conversación con rol, contenido, adjuntos, métricas y relación opcional con una ejecución.

## Memoria

Información persistente recuperable por ámbito. No equivale al historial completo ni concede permisos.

## Ámbito o scope

Límite de visibilidad y aplicación de un recurso. Puede ser global, usuario, proyecto, agente o conversación.

## Proyecto

Espacio lógico de aislamiento dentro del Core para recursos, memoria, conversaciones, agentes y credenciales de un cliente o iniciativa.

## Approval

Decisión humana requerida antes de ejecutar una operación riesgosa.

## Risk level

Clasificación del impacto potencial de una herramienta: read-only, low, medium, high o critical.

## Secret

Dato sensible cifrado y redactado en respuestas y logs. Nunca se almacena como texto plano en configuración de dominio.

## Evento

Hecho inmutable emitido por un módulo, por ejemplo `task.completed`. No es una orden.

## Comando

Solicitud explícita para ejecutar una acción. Puede ser rechazada por validación o permisos.

## Outbox

Patrón para persistir cambios de dominio y eventos pendientes en la misma transacción antes de publicarlos.

## Streaming

Entrega incremental de datos durante una operación, como tokens de chat o progreso de una tarea.

## Correlation ID

Identificador que permite rastrear una operación a través de API, worker, provider, eventos y logs.

## Idempotency key

Clave enviada por un cliente para evitar la duplicación accidental de una operación.

## Healthcheck

Comprobación de vida básica del proceso.

## Readiness

Comprobación de que el servicio está listo para recibir trabajo y que sus dependencias críticas están disponibles.

## Foundation Build

Primera versión funcional y extensible del Core definida en la documentación. No es una maqueta ni incluye todas las integraciones futuras.

## ADR

Architecture Decision Record. Documento inmutable que registra contexto, decisión, consecuencias y estado de una decisión técnica relevante.

## Deuda técnica aceptada

Limitación consciente, documentada, acotada y con motivo. No incluye código roto, TODOs indefinidos ni funcionalidades falsas.
