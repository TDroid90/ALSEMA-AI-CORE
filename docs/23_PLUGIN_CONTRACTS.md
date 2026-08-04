# 23 — Contratos de Plugins

## Objetivo

Definir contratos ejecutables y estables para extender ALSEMA AI CORE sin introducir acoplamiento entre el núcleo y las integraciones futuras.

## Principios

1. Un plugin amplía capacidades; no modifica el dominio central.
2. Los plugins no se importan entre sí.
3. Todo plugin declara permisos, configuración y capacidades antes de activarse.
4. El Core controla carga, aislamiento, auditoría y ciclo de vida.
5. Ningún plugin puede ejecutar código arbitrario por defecto.

## Estructura mínima

```text
plugins/<plugin_id>/
├── manifest.json
├── plugin.py
├── schemas.py
├── settings.py
├── tools/
├── nodes/
├── migrations/
├── tests/
└── README.md
```

## Manifest

Campos obligatorios:

- `id`: identificador global en kebab-case.
- `name`: nombre visible.
- `version`: SemVer.
- `core_version`: rango compatible.
- `description`.
- `author`.
- `entrypoint`.
- `capabilities`.
- `permissions`.
- `settings_schema`.
- `healthcheck`.

Ejemplo:

```json
{
  "id": "generic-http",
  "name": "Generic HTTP",
  "version": "1.0.0",
  "core_version": ">=1.0.0 <2.0.0",
  "entrypoint": "plugin:GenericHttpPlugin",
  "capabilities": ["tools", "workflow_nodes"],
  "permissions": ["network.outbound"],
  "settings_schema": "schemas:PluginSettings",
  "healthcheck": "plugin:healthcheck"
}
```

## Contrato principal

```python
class Plugin(Protocol):
    metadata: PluginMetadata

    async def install(self, context: PluginInstallContext) -> None: ...
    async def activate(self, context: PluginRuntimeContext) -> None: ...
    async def deactivate(self, context: PluginRuntimeContext) -> None: ...
    async def uninstall(self, context: PluginInstallContext) -> None: ...
    async def healthcheck(self) -> PluginHealth: ...
```

## Registro de capacidades

El plugin podrá registrar únicamente capacidades declaradas en el manifest:

- Tools.
- Workflow nodes.
- Event handlers.
- Scheduled jobs.
- API routes bajo namespace propio.
- UI navigation extensions futuras.
- Provider adapters futuros.

Toda capacidad deberá tener un identificador namespaced:

```text
generic-http.request
filesystem.read-text
python.execute-restricted
```

## Permisos

Permisos iniciales:

- `network.outbound`
- `network.inbound`
- `filesystem.read`
- `filesystem.write`
- `database.read`
- `database.write`
- `process.execute`
- `secrets.read`
- `events.publish`
- `events.subscribe`

La activación de un plugin con permisos críticos requiere aprobación administrativa explícita.

## Configuración y secretos

- La configuración pública se valida con Pydantic.
- Los secretos nunca se guardan en el manifest.
- Los secretos se almacenan cifrados mediante el servicio central de secretos.
- El plugin recibe referencias resueltas solo durante ejecución.
- Los secretos no aparecen en logs, excepciones ni respuestas API.

## Migraciones

Un plugin puede incluir migraciones propias si necesita persistencia.

Reglas:

- Tabla con prefijo `plugin_<plugin_id_normalizado>_`.
- No modificar tablas de otros módulos.
- Migraciones versionadas y reversibles cuando sea razonable.
- El Core registra la versión aplicada.

## Estados

```text
DISCOVERED → VALIDATED → INSTALLED → ACTIVE
                              ↓         ↓
                           FAILED ← DISABLED
                              ↓
                          UNINSTALLED
```

## Fallos

Un fallo de plugin no debe detener el Core.

El sistema debe:

- aislar la excepción;
- marcar el plugin como degradado;
- registrar un evento de auditoría;
- deshabilitar temporalmente capacidades inseguras;
- permitir reintento manual.

## Plugin SDK

El repositorio deberá incluir un paquete interno `alsema_plugin_sdk` con:

- tipos y protocolos;
- decoradores de registro;
- clientes seguros para eventos y secretos;
- utilidades de testing;
- ejemplo mínimo funcional.

## Plugins funcionales de Foundation Build

1. `generic-http`: solicitudes HTTP controladas.
2. `filesystem`: lectura y escritura dentro de sandbox configurado.
3. `python-restricted`: ejecución limitada mediante worker aislado.
4. `ollama-provider`: adaptador del proveedor inicial.

## Criterios de aceptación

- El Core descubre plugins sin importarlos de forma insegura.
- Un manifest inválido se rechaza con explicación.
- Activar y desactivar un plugin no requiere reiniciar toda la plataforma cuando sea técnicamente viable.
- Los permisos se muestran antes de activar.
- Un plugin con fallo no derriba la API.
- Las herramientas registradas aparecen en la biblioteca global.
- Los logs identifican `plugin_id` y versión.
