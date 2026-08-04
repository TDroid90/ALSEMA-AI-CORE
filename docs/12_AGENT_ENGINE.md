# 12 — Agent Engine

## Objetivo

El Agent Engine administra agentes configurables y reutilizables. Un agente combina instrucciones, perfil de inferencia, herramientas autorizadas, memoria y contrato de salida. No debe confundirse con una personalidad superficial ni con un prompt guardado.

## Alcance del Foundation Build

Implementar:

- CRUD de agentes;
- versionado inmutable;
- borrador y publicación;
- selección de proveedor/modelo mediante inference profile;
- prompt de sistema;
- herramientas autorizadas;
- política de memoria;
- salida libre o JSON Schema;
- ejecución en chat;
- registros de uso;
- duplicación y exportación/importación JSON;
- desactivación.

Fuera de alcance:

- equipos multiagente autónomos;
- planificación recursiva ilimitada;
- aprendizaje automático del prompt;
- agentes empresariales específicos;
- acceso implícito a Internet o filesystem.

## Principios

1. El agente nunca conoce directamente Ollama.
2. Toda ejecución referencia una versión concreta e inmutable.
3. Las herramientas están denegadas por defecto.
4. El agente no puede elevar sus propios permisos.
5. La memoria se recupera por política explícita.
6. Toda salida estructurada se valida.
7. Los ciclos de herramientas tienen un límite.
8. Los fallos son observables y reproducibles.
9. Las instrucciones del sistema prevalecen sobre contenido externo.
10. Ningún agente puede ejecutar acciones destructivas sin autorización adicional.

## Entidades

### Agent

Identidad estable:

- key;
- nombre;
- descripción;
- estado;
- versión actual publicada.

### AgentVersion

Configuración inmutable:

- número de versión;
- system prompt;
- inference profile;
- herramientas;
- política de memoria;
- política de ejecución;
- esquema de salida;
- nota de cambio;
- autor;
- fecha de publicación.

### AgentRun

Ejecución concreta:

- agente y versión;
- usuario;
- conversación o tarea;
- inputs;
- provider/model resuelto;
- herramientas llamadas;
- consumo;
- resultado;
- estado y errores.

## Estados

Agent:

- `draft`
- `active`
- `disabled`
- `archived`

AgentVersion:

- `draft`
- `published`
- `superseded`

Una versión publicada no se edita. Cualquier cambio crea una versión nueva.

## Inference Profile

El agente referencia un perfil, no parámetros sueltos duplicados.

Incluye:

- provider connection;
- model;
- temperature;
- top_p;
- max output tokens;
- timeout;
- opciones específicas controladas.

La resolución final debe verificar que el modelo continúe disponible. Si no está disponible, devolver error claro; no cambiar silenciosamente de modelo salvo fallback configurado.

## Construcción del contexto

Orden obligatorio:

1. políticas globales del Core;
2. system prompt de la versión;
3. instrucciones de herramientas;
4. memoria recuperada y marcada como contexto no confiable cuando corresponda;
5. historial acotado de conversación;
6. mensaje actual del usuario.

Nunca concatenar documentos externos como si fueran instrucciones del sistema.

## Política de memoria

Campos mínimos:

- scopes permitidos;
- cantidad máxima de entradas;
- límite aproximado de tokens;
- tipos de memoria;
- estrategia de ordenamiento;
- permiso para escribir memoria;
- expiración por defecto.

Foundation Build usa búsqueda textual y filtros. La política debe quedar preparada para un retriever semántico futuro.

## Tool Calling

Ciclo controlado:

1. enviar contexto y definiciones de herramientas al proveedor;
2. recibir respuesta o solicitud de herramienta;
3. validar nombre y argumentos;
4. verificar permisos del usuario, agente y plugin;
5. evaluar riesgo y aprobación requerida;
6. ejecutar con timeout;
7. redactar resultado sensible;
8. agregar resultado al contexto;
9. continuar hasta respuesta final o límite.

Límites configurables:

- máximo de llamadas por turno;
- máximo de profundidad;
- timeout total;
- presupuesto de tokens;
- tamaño máximo de resultados.

Si se alcanza un límite, finalizar con error controlado o respuesta parcial explícita.

## Salida estructurada

Cuando existe `output_schema`:

- solicitar JSON estricto si el proveedor lo soporta;
- parsear;
- validar con JSON Schema/Pydantic;
- permitir un número bajo y configurable de reparaciones;
- conservar el texto bruto para diagnóstico restringido;
- no aceptar campos inventados fuera del schema si `additionalProperties=false`.

Errores:

- `AGENT_OUTPUT_PARSE_FAILED`
- `AGENT_OUTPUT_VALIDATION_FAILED`
- `AGENT_OUTPUT_REPAIR_EXHAUSTED`

## Streaming

Para chat:

- transmitir deltas de texto;
- emitir eventos de inicio y finalización;
- pausar streaming durante aprobación de herramienta;
- emitir eventos de herramienta sin exponer secretos;
- persistir el mensaje final consolidado;
- marcar mensajes incompletos si se cancela.

## Prompts

El system prompt debe escribirse como contrato operativo. La UI debe ofrecer:

- editor monoespaciado;
- conteo aproximado de tokens;
- variables soportadas;
- vista previa de contexto;
- historial de versiones;
- diferencia entre versiones;
- botón de prueba aislada.

No introducir un lenguaje de plantillas complejo en v1. Variables iniciales seguras:

- `{{current_date}}`
- `{{user_display_name}}`
- `{{conversation_title}}`
- `{{project_scope}}`

Los valores se escapan y no pueden ejecutar código.

## Ejecución síncrona y durable

Chat normal puede iniciar como request con streaming, pero debe registrar un AgentRun durable.

Procesamientos largos deben convertirse en Task:

- el endpoint responde `202`;
- el worker ejecuta;
- progreso por eventos;
- resultado recuperable;
- cancelación cooperativa.

## Seguridad contra prompt injection

- contenido de usuario y herramientas se considera no confiable;
- secretos no forman parte del prompt;
- las herramientas verifican permisos fuera del LLM;
- frases como “ignorá instrucciones anteriores” no alteran políticas del Core;
- resultados web/archivos se delimitan como datos;
- acciones externas requieren política explícita.

## Observabilidad

Registrar:

- agent_id y version_id;
- provider/model;
- duración;
- tokens si están disponibles;
- cantidad de tool calls;
- códigos de error;
- correlation_id;
- estado final.

No registrar prompts completos por defecto. Debe existir una modalidad de diagnóstico controlada, con redacción y vencimiento.

## Importación y exportación

Formato JSON versionado que incluya:

- identidad descriptiva;
- configuración de la versión;
- referencias lógicas de herramientas;
- inference profile lógico;
- schemas;
- metadatos.

No exportar secretos, IDs internos dependientes de una instalación ni credenciales.

## API mínima

- `GET /api/v1/agents`
- `POST /api/v1/agents`
- `GET /api/v1/agents/{id}`
- `PATCH /api/v1/agents/{id}`
- `POST /api/v1/agents/{id}/versions`
- `POST /api/v1/agents/{id}/versions/{version}/publish`
- `POST /api/v1/agents/{id}/test`
- `POST /api/v1/agents/{id}/duplicate`
- `GET /api/v1/agents/{id}/export`
- `POST /api/v1/agents/import`

## UI mínima

- listado con estado, modelo y versión;
- editor por secciones;
- selección de herramientas con nivel de riesgo;
- configuración de memoria;
- schema de salida;
- prueba interactiva;
- historial y diff de versiones;
- publicación explícita.

## Criterios de aceptación

- Crear un agente borrador.
- Publicar su primera versión.
- Usarlo en una conversación con Ollama.
- Crear una segunda versión sin alterar la primera.
- Validar una salida JSON.
- Rechazar una herramienta no autorizada.
- Detener un loop por límite.
- Registrar ejecución y consumo.
- Desactivar un agente sin borrar historial.
