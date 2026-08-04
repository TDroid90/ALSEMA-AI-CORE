# 10 — Backend Structure

## Objetivo

Definir una estructura de backend clara para que Codex implemente ALSEMA AI CORE como monolito modular, evitando carpetas genéricas sin límites de dominio.

## Estructura raíz

```text
backend/
├── pyproject.toml
├── alembic.ini
├── app/
│   ├── main.py
│   ├── bootstrap.py
│   ├── config/
│   ├── shared/
│   ├── modules/
│   ├── api/
│   └── workers/
├── migrations/
└── tests/
```

## `app/main.py`

Responsabilidades permitidas:

- crear la instancia FastAPI;
- registrar middleware;
- registrar routers versionados;
- registrar handlers globales de error;
- registrar eventos de ciclo de vida;
- exponer OpenAPI.

No contiene lógica de negocio, acceso directo a base de datos ni llamadas a proveedores.

## `app/bootstrap.py`

Composition root de la aplicación.

Debe ensamblar:

- configuración;
- conexiones de base de datos y Redis;
- repositorios;
- servicios de aplicación;
- adaptadores de proveedores;
- registro de herramientas;
- registro de plugins;
- buses de eventos;
- clientes HTTP;
- observabilidad.

La inyección de dependencias será explícita. No usar un service locator global oculto.

## Configuración

```text
app/config/
├── settings.py
├── logging.py
├── security.py
└── constants.py
```

`settings.py` usa Pydantic Settings y valida todas las variables al iniciar. Debe existir `.env.example` completo, sin secretos reales.

Configuraciones mínimas:

- entorno;
- URL de PostgreSQL;
- URL de Redis;
- claves de firma;
- credenciales de administrador inicial;
- URL de Ollama;
- CORS;
- límites de carga;
- timeouts;
- políticas de retención;
- nivel de logs.

## Shared kernel

```text
app/shared/
├── domain/
│   ├── entity.py
│   ├── value_object.py
│   ├── events.py
│   └── errors.py
├── application/
│   ├── command.py
│   ├── query.py
│   ├── pagination.py
│   └── result.py
├── infrastructure/
│   ├── database.py
│   ├── redis.py
│   ├── http.py
│   ├── crypto.py
│   └── clock.py
└── observability/
    ├── logging.py
    ├── metrics.py
    └── tracing.py
```

El shared kernel debe mantenerse pequeño. No mover lógica de negocio aquí por comodidad.

## Módulos

```text
app/modules/
├── identity/
├── access/
├── providers/
├── models/
├── conversations/
├── agents/
├── tools/
├── plugins/
├── workflows/
├── tasks/
├── memory/
├── audit/
├── settings/
└── system/
```

Cada módulo utiliza la misma estructura interna solo cuando la necesita:

```text
<module>/
├── domain/
│   ├── entities.py
│   ├── value_objects.py
│   ├── events.py
│   ├── policies.py
│   └── repository.py
├── application/
│   ├── commands/
│   ├── queries/
│   ├── dto.py
│   └── services.py
├── infrastructure/
│   ├── models.py
│   ├── repository.py
│   ├── adapters.py
│   └── mappers.py
└── presentation/
    ├── schemas.py
    └── router.py
```

No crear archivos vacíos para aparentar DDD. La estructura aparece cuando existe una responsabilidad real.

## Límites de dependencia

Dependencias permitidas:

```text
presentation -> application -> domain
infrastructure -> domain
bootstrap -> todos los módulos
```

Dependencias prohibidas:

- domain hacia FastAPI, SQLAlchemy, Redis o HTTP;
- un módulo importando modelos SQLAlchemy privados de otro;
- routers llamando directamente a repositorios;
- adaptadores de proveedor escribiendo directamente en tablas de conversaciones;
- plugins accediendo a objetos internos no publicados.

Los módulos colaboran mediante:

- servicios públicos de aplicación;
- puertos/interfaces;
- eventos de dominio o integración;
- DTOs estables.

## API

```text
app/api/
├── v1/
│   ├── router.py
│   └── dependencies.py
├── middleware/
│   ├── request_id.py
│   ├── auth.py
│   ├── rate_limit.py
│   └── audit_context.py
└── errors.py
```

Cada módulo registra su router en `api/v1/router.py`. No concentrar todos los endpoints en un único archivo.

## Workers

```text
app/workers/
├── arq.py
├── registry.py
├── context.py
└── jobs/
```

Los jobs ARQ son adaptadores delgados. Deben:

1. resolver el servicio de aplicación apropiado;
2. cargar la tarea durable desde PostgreSQL;
3. ejecutar el caso de uso;
4. guardar progreso y resultado;
5. emitir eventos;
6. manejar retry según política.

No deben contener lógica empresarial extensa.

## Transacciones

Usar Unit of Work por caso de uso cuando una operación modifica varias entidades.

Reglas:

- una transacción no debe envolver una llamada LLM larga;
- persistir intención antes de enviar a cola;
- persistir resultados después de cada punto de control importante;
- usar locks explícitos solo cuando haya riesgo demostrado de concurrencia;
- aplicar control optimista a recursos editables/versionados.

## Integración con Ollama

```text
app/modules/providers/infrastructure/ollama/
├── client.py
├── adapter.py
├── mapper.py
└── errors.py
```

El cliente HTTP conoce Ollama. El resto del Core conoce interfaces de capacidad como:

- `ChatProvider`
- `ModelCatalogProvider`
- `EmbeddingProvider` en una fase futura

El adaptador convierte errores externos a errores internos estables.

## Eventos

Foundation Build utiliza un bus interno en proceso para eventos inmediatos y Redis Pub/Sub o Streams para notificaciones de progreso cuando corresponda.

Todo evento debe incluir:

- event_id;
- event_type;
- occurred_at;
- aggregate_id o resource_id;
- correlation_id;
- actor_id cuando exista;
- payload versionado.

No introducir Kafka ni un broker adicional en v1.

## Manejo de errores

Jerarquía base:

- `DomainError`
- `ValidationError`
- `NotFoundError`
- `ConflictError`
- `PermissionDeniedError`
- `ExternalProviderError`
- `TransientError`
- `TaskCancelledError`

Los adaptadores traducen excepciones externas. Los handlers API traducen errores internos al contrato definido en `06_API_CONVENTIONS.md`.

Nunca devolver stack traces al cliente.

## Observabilidad

Cada request, tarea, workflow y ejecución de herramienta debe compartir:

- `request_id`;
- `correlation_id`;
- `task_id` cuando corresponda;
- `user_id` cuando corresponda.

Logs JSON en backend. Logs legibles en desarrollo pueden derivarse mediante formatter, sin cambiar los campos estructurados.

## Pruebas

```text
tests/
├── unit/
├── integration/
├── contract/
├── api/
└── fixtures/
```

- unitarias para dominio y políticas;
- integración para repositorios y adaptadores;
- contratos para proveedores y plugins;
- API para endpoints y autorización;
- end-to-end para flujos de aceptación críticos.

## Calidad obligatoria

Antes de aceptar una fase:

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

No silenciar tipos con `Any` indiscriminado. No agregar excepciones globales de lint para evitar arreglar código.

## Criterios de aceptación

- La aplicación inicia desde un único composition root.
- Ningún router ejecuta SQL directo.
- El dominio no importa frameworks.
- Ollama puede reemplazarse por un fake en pruebas.
- Los jobs son reiniciables e idempotentes según su caso.
- Cada módulo expone una superficie pública definida.
- Las dependencias circulares están ausentes y verificadas en CI.
