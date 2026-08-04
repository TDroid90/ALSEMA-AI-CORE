# 11 — Plugin System

## Objetivo

El sistema de plugins permite extender ALSEMA AI CORE sin incorporar lógica empresarial al núcleo ni permitir que extensiones externas accedan libremente a internals sensibles.

Un plugin es un paquete versionado que declara capacidades, configuración, permisos y puntos de extensión. No es una carpeta arbitraria de scripts.

## Alcance del Foundation Build

Implementar completamente:

- descubrimiento de plugins instalados localmente;
- lectura y validación de manifest;
- habilitar y deshabilitar plugins;
- configuración no secreta;
- resolución segura de secretos;
- registro de herramientas;
- healthcheck;
- logs y auditoría;
- plugin HTTP genérico;
- plugin de filesystem acotado;
- plugin Python sandboxed de alcance limitado, solo si puede implementarse con seguridad suficiente; de lo contrario documentar y omitir.

Preparar, pero no integrar:

- Google Sheets;
- Google Drive;
- Telegram;
- Facebook;
- Instagram;
- WhatsApp;
- generación de imágenes;
- generación de audio.

## Principios

1. Un plugin depende del SDK público del Core, no de módulos internos.
2. Ningún plugin importa modelos SQLAlchemy del Core.
3. Todos los permisos son declarativos y denegados por defecto.
4. La instalación no implica habilitación.
5. La habilitación no implica acceso a todos los usuarios o agentes.
6. Los secretos no se exponen a la interfaz ni a logs.
7. Un fallo de plugin no debe derribar la API.
8. Los manifests son versionados y validados antes de cargar código.
9. Las extensiones peligrosas requieren confirmación y auditoría.
10. El Core puede revocar un plugin inmediatamente.

## Estructura de un plugin

```text
plugins/<plugin_key>/
├── plugin.toml
├── README.md
├── src/
│   └── <package>/
├── tests/
└── pyproject.toml
```

En v1, los plugins oficiales pueden vivir en el monorepo, pero deben consumir el mismo SDK que usaría un plugin externo.

## Manifest

Ejemplo conceptual:

```toml
manifest_version = "1"
key = "core.http"
name = "HTTP Client"
version = "1.0.0"
description = "Performs controlled HTTP requests"
minimum_core_version = "0.1.0"
entrypoint = "alsema_plugin_http:plugin"

[capabilities]
tools = true
workflows = true
healthcheck = true

[permissions]
network = ["https"]
filesystem = []
shell = false
python = false
secrets = ["http.auth"]
```

Campos obligatorios:

- versión de manifest;
- clave única;
- nombre y versión semántica;
- versión mínima y máxima compatible del Core;
- entrypoint;
- capacidades;
- permisos solicitados;
- esquema de configuración;
- migraciones propias si correspondieran.

## Contrato del SDK

El Core publicará tipos estables para:

- `Plugin`
- `PluginManifest`
- `PluginContext`
- `ToolRegistration`
- `WorkflowNodeRegistration`
- `HealthcheckResult`
- `SecretReference`
- `AuditEmitter`
- `Logger`

El `PluginContext` ofrece únicamente capacidades autorizadas. No entrega una sesión SQL, el contenedor de dependencias completo ni acceso al sistema operativo.

## Ciclo de vida

Estados:

- `discovered`
- `incompatible`
- `installed`
- `disabled`
- `enabling`
- `enabled`
- `degraded`
- `failed`
- `uninstalling`

Flujo normal:

1. descubrir;
2. validar manifest;
3. verificar compatibilidad;
4. mostrar permisos;
5. instalar;
6. configurar;
7. ejecutar healthcheck;
8. habilitar;
9. registrar capacidades.

Deshabilitar un plugin debe impedir nuevas ejecuciones sin destruir historial.

## Registro de herramientas

Cada herramienta declara:

- key estable;
- nombre y descripción;
- JSON Schema de entrada;
- JSON Schema de salida;
- nivel de riesgo;
- permisos requeridos;
- timeout;
- política de retry;
- idempotencia;
- redactores de entrada y salida;
- executor.

El Core valida que no existan claves duplicadas y conserva la procedencia del plugin.

## Niveles de riesgo

- `read_only`: consulta sin efectos externos.
- `bounded_write`: escribe dentro de un recurso limitado.
- `external_write`: modifica un sistema externo.
- `code_execution`: ejecuta código o shell.
- `destructive`: elimina o altera de forma difícil de revertir.

Los niveles `code_execution` y `destructive` no pueden quedar habilitados automáticamente.

## Configuración y secretos

La configuración se divide en:

- pública: visible y editable;
- sensible: visible parcialmente;
- secreta: almacenada cifrada o referenciada desde entorno.

La API nunca devuelve secretos. Debe responder si están configurados y su fecha de actualización, no su valor.

## Aislamiento

Foundation Build no promete aislamiento fuerte de procesos para plugins Python instalados localmente. Por eso:

- solo se habilitan plugins confiables;
- el panel muestra claramente el nivel de confianza;
- se limita la superficie del contexto;
- se aplican timeouts;
- se auditan ejecuciones;
- el futuro aislamiento en workers o contenedores se documentará mediante ADR.

No afirmar que existe sandbox seguro si el código se ejecuta en el mismo proceso.

## Plugin HTTP oficial

Debe ofrecer una herramienta de request controlada:

- métodos permitidos configurables;
- allowlist/denylist de hosts;
- bloqueo de direcciones privadas por defecto para prevenir SSRF;
- límite de tamaño de respuesta;
- timeout;
- headers secretos por referencia;
- redacción de credenciales;
- sin seguimiento automático de redirects hacia destinos prohibidos.

## Plugin Filesystem oficial

Debe operar solo dentro de roots configurados.

- impedir path traversal;
- resolver symlinks y validar destino;
- límite de tamaño;
- extensiones permitidas configurables;
- lectura y escritura separadas por permiso;
- sin acceso al home completo por defecto;
- eliminación deshabilitada inicialmente.

## Integración con workflows

Un plugin puede registrar nodos, pero el motor conserva:

- validación del grafo;
- ejecución y estado;
- retries;
- auditoría;
- cancelación;
- control de permisos.

El plugin implementa la capacidad, no el orquestador.

## Versionado y compatibilidad

- manifests usan versionado semántico;
- cambios incompatibles del SDK requieren major version;
- versiones instaladas quedan registradas en ejecuciones históricas;
- una actualización debe ejecutar healthcheck antes de activarse;
- si falla, conservar la versión anterior cuando sea técnicamente posible.

## Errores

Errores estables:

- `PLUGIN_NOT_FOUND`
- `PLUGIN_INCOMPATIBLE`
- `PLUGIN_DISABLED`
- `PLUGIN_CONFIGURATION_INVALID`
- `PLUGIN_PERMISSION_DENIED`
- `PLUGIN_HEALTHCHECK_FAILED`
- `PLUGIN_EXECUTION_FAILED`
- `PLUGIN_TIMEOUT`

## Criterios de aceptación

- El Core detecta y valida un plugin oficial.
- Un manifest inválido no carga código.
- Deshabilitar un plugin bloquea nuevas ejecuciones.
- Una herramienta no puede usar permisos no declarados.
- Los secretos no aparecen en responses ni logs.
- El plugin HTTP bloquea SSRF básico.
- El filesystem no escapa de los roots autorizados.
- El fallo de un plugin se refleja como degradación y no detiene el servidor.
