# 24 — Catálogo Inicial de Nodos de Workflow

## Objetivo

Delimitar el conjunto de nodos realmente funcionales del Foundation Build. La primera versión no intentará replicar n8n: entregará un motor pequeño, verificable y extensible.

## Reglas generales

Cada nodo debe declarar:

- `type` y versión.
- Esquema de entrada.
- Esquema de salida.
- Configuración validada.
- Política de reintento.
- Timeout.
- Nivel de riesgo.
- Requisitos de permisos.
- Estrategia de idempotencia.
- Eventos emitidos.

## Contrato

```python
class WorkflowNode(Protocol):
    definition: NodeDefinition

    async def validate(self, configuration: dict) -> ValidationResult: ...
    async def execute(self, context: NodeExecutionContext) -> NodeResult: ...
    async def compensate(self, context: NodeCompensationContext) -> None: ...
```

La compensación será opcional y se implementará solo cuando el nodo produzca efectos reversibles.

## Nodos Foundation Build

### 1. Manual Trigger

Inicia un workflow desde la interfaz o API.

Salida:

```json
{"triggered_by": "user_id", "payload": {}}
```

### 2. Schedule Trigger

Ejecuta según expresión cron validada.

Requisitos:

- zona horaria explícita;
- prevención de ejecuciones duplicadas;
- posibilidad de pausar;
- registro de próxima ejecución.

### 3. Webhook Trigger

Recibe una solicitud autenticada bajo endpoint namespaced.

Requisitos:

- secreto o firma;
- límite de tamaño;
- rate limit;
- protección contra replay cuando corresponda.

### 4. LLM Generate

Ejecuta una generación mediante `LLMProvider`.

Configuración:

- proveedor/modelo o perfil de inferencia;
- prompt del sistema;
- template del usuario;
- temperatura;
- límite de tokens;
- formato de salida opcional.

### 5. Agent Run

Ejecuta una versión publicada de un agente con sus herramientas autorizadas.

### 6. HTTP Request

Solicitud HTTP saliente mediante el plugin `generic-http`.

Debe soportar:

- métodos comunes;
- headers y query params;
- body JSON o texto;
- secretos por referencia;
- timeout;
- lista de hosts permitidos;
- tamaño máximo de respuesta.

### 7. Read Text File

Lee texto dentro de un workspace permitido.

Nunca acepta rutas fuera del sandbox configurado.

### 8. Write Text File

Escribe texto de forma atómica dentro del sandbox.

Debe permitir política: crear, reemplazar o fallar si existe.

### 9. Python Restricted

Ejecuta código Python bajo límites explícitos.

Foundation Build:

- proceso aislado;
- tiempo máximo;
- memoria máxima cuando el host lo permita;
- sin red por defecto;
- directorio temporal;
- lista de módulos permitidos;
- captura de stdout/stderr.

### 10. Condition

Evalúa expresiones declarativas seguras, sin `eval`.

Operadores:

- igualdad/desigualdad;
- comparación numérica;
- contiene;
- existe;
- AND/OR/NOT.

### 11. Transform

Mapea y renombra campos mediante una sintaxis declarativa.

### 12. Loop Items

Itera sobre una colección con límite máximo configurable.

Debe controlar:

- concurrencia;
- número máximo de elementos;
- política ante error individual;
- agregación final.

### 13. Delay

Pausa durable hasta una fecha o por un intervalo. No debe mantener un worker bloqueado.

### 14. Approval

Detiene el workflow y solicita aprobación humana.

Incluye:

- motivo;
- resumen de efectos;
- vencimiento;
- usuarios o roles autorizados;
- aprobar/rechazar.

### 15. Set Output

Define la salida pública final del workflow.

## Modelo de conexiones

- Los puertos tienen esquemas tipados.
- El editor impide conexiones claramente incompatibles.
- La validación definitiva ocurre en backend.
- Un nodo puede tener salidas `success`, `failure` y salidas específicas.
- Los ciclos solo se permiten mediante el nodo Loop; no mediante conexiones arbitrarias.

## Expresiones y plantillas

Se utilizará una sintaxis limitada, por ejemplo:

```text
{{ trigger.payload.product_name }}
{{ nodes.generate.output.text }}
```

No permitir acceso a objetos internos, atributos mágicos ni ejecución de funciones arbitrarias.

## Persistencia de ejecución

Por cada nodo:

- estado;
- intento;
- inicio y fin;
- input saneado;
- output saneado;
- error estructurado;
- métricas;
- artefactos;
- referencia a logs.

## Criterios de aceptación

- Un workflow manual de tres nodos puede crearse, validarse y ejecutarse.
- Un fallo muestra el nodo exacto y permite reintento desde un punto seguro.
- Delay sobrevive al reinicio.
- Approval pausa y reanuda correctamente.
- Los datos sensibles quedan redactados.
- La interfaz muestra progreso por nodo.
- Los nodos desconocidos impiden publicar, pero no destruyen la definición guardada.
