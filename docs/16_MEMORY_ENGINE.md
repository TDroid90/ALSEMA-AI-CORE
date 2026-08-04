# 16 — Memory Engine

## Propósito

Definir una memoria persistente, segura y auditable para conversaciones, agentes, proyectos y usuarios, sin convertir el Foundation Build en una plataforma RAG compleja.

## Tipos de memoria

### Conversacional

Mensajes y resúmenes necesarios para continuar una conversación.

### De agente

Preferencias operativas, instrucciones y contexto estable asociado a una versión de agente.

### De proyecto

Contexto compartido por clientes o espacios de trabajo futuros.

### De usuario

Preferencias permitidas y contexto personal explícitamente persistido.

### Global

Conocimiento operativo del Core autorizado para todos los ámbitos compatibles.

## Principios

1. Toda memoria tiene propietario y ámbito.
2. Nada se recuerda de forma implícita sin política definida.
3. El usuario puede inspeccionar, corregir y eliminar memoria autorizada.
4. La memoria recuperada se trata como datos, no como instrucciones privilegiadas.
5. La memoria no debe romper aislamiento entre proyectos o usuarios.
6. Los cambios quedan auditados.

## Entidad MemoryRecord

Campos mínimos:

- `id`
- `scope_type`
- `scope_id`
- `owner_user_id`
- `content`
- `content_type`
- `source_type`
- `source_id`
- `status`
- `importance`
- `expires_at`
- `created_at`
- `updated_at`
- `deleted_at`
- `metadata_json`

## Recuperación v1

El Foundation Build implementará recuperación básica por:

- ámbito;
- texto;
- etiquetas;
- fecha;
- importancia;
- estado.

Los embeddings y búsqueda vectorial podrán agregarse mediante una estrategia independiente, pero no son requisito para declarar la memoria básica operativa.

## Context assembly

Antes de invocar un modelo:

1. Determinar ámbitos permitidos.
2. Consultar recuerdos candidatos.
3. Aplicar límites de cantidad y tokens.
4. Ordenar por relevancia determinística disponible.
5. Marcar el bloque como contexto no confiable.
6. Registrar qué IDs fueron utilizados.

## Escritura

La memoria puede escribirse por:

- acción explícita del usuario;
- regla de agente autorizada;
- workflow autorizado;
- resumen conversacional automático configurado.

Las escrituras automáticas deben indicar origen y motivo.

## Expiración

- TTL opcional.
- Limpieza programada.
- Estado `expired` antes de eliminación física cuando corresponda.
- Las referencias históricas no deben romperse.

## Eliminación

- Soft delete por defecto.
- Purga definitiva administrativa cuando sea requerida.
- Cascadas controladas.
- Registro de auditoría.

## Riesgos

### Prompt injection persistente

El contenido recuperado nunca se interpreta como prompt de sistema.

### Contaminación entre ámbitos

Toda consulta exige filtros de scope y permisos en backend.

### Crecimiento sin límite

Aplicar cuotas, TTL, compactación y resúmenes.

### Memoria incorrecta

Permitir edición, desactivación y trazabilidad de fuente.

## Compactación conversacional

Cuando el contexto exceda umbrales:

- generar resumen estructurado;
- conservar hitos y decisiones;
- registrar rango de mensajes resumidos;
- no eliminar mensajes originales automáticamente;
- permitir reconstrucción y auditoría.

## API mínima

- listar recuerdos autorizados;
- crear recuerdo;
- editar recuerdo;
- desactivar o eliminar;
- buscar;
- inspeccionar procedencia;
- consultar usos recientes.

## Pruebas

- aislamiento por usuario;
- aislamiento por proyecto;
- TTL;
- soft delete;
- ensamblado con límite de tokens;
- intento de acceso cruzado;
- contenido con instrucciones maliciosas;
- auditoría de escritura automática.

## Criterios de aceptación

- La memoria persiste tras reinicio.
- Los ámbitos se respetan.
- El usuario puede inspeccionar y corregir.
- El sistema registra qué memoria inyectó.
- El contenido recuperado no obtiene privilegios de sistema.
- El Core funciona sin vector store.
