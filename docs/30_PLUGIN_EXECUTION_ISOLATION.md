# Plugin Execution Isolation

## Decisión

ALSEMA AI CORE autoriza el aislamiento de plugins mediante contenedores efímeros de Docker con acceso mínimo y controlado.

Esta decisión aplica a plugins y herramientas capaces de ejecutar Python, shell o código externo.

## Principio de seguridad

El backend principal no debe recibir acceso directo e irrestricto al daemon Docker.

Queda prohibido:

- usar `privileged: true`;
- montar `/var/run/docker.sock` dentro del backend principal;
- permitir imágenes arbitrarias indicadas por el usuario;
- montar carpetas arbitrarias del host;
- exponer secretos globales a los contenedores de ejecución;
- permitir acceso de red por defecto.

## Abstracción requerida

Implementar una interfaz `PluginExecutionRuntime` desacoplada del motor de plugins.

Debe soportar inicialmente dos modos:

### `in_process`

Solo para plugins internos confiables.

- desactivado por defecto en producción;
- no apto para código externo;
- sujeto a permisos y auditoría.

### `docker_sandbox`

Modo obligatorio para plugins que ejecuten Python, shell o código aportado externamente.

Cada ejecución debe crear un contenedor nuevo y eliminarlo al finalizar.

## Restricciones del sandbox

Cada contenedor efímero debe ejecutarse con:

- usuario no root;
- filesystem raíz de solo lectura;
- directorio temporal aislado y descartable;
- sin acceso a carpetas del host salvo mounts explícitos de solo lectura aprobados;
- sin secretos globales;
- sin modo privilegiado;
- sin acceso directo al socket Docker;
- capacidades Linux eliminadas mediante `cap_drop`;
- límite configurable de CPU;
- límite configurable de RAM;
- límite de procesos;
- timeout duro;
- cancelación forzada;
- red desactivada por defecto;
- allowlist explícita para plugins que necesiten red;
- imágenes base aprobadas por configuración;
- captura de stdout, stderr, código de salida, duración y metadatos;
- auditoría completa de inicio, resultado, cancelación y error;
- eliminación automática del contenedor y archivos temporales.

## Arquitectura recomendada

Separar la capacidad de ejecución del backend mediante un servicio interno denominado, por ejemplo, `plugin-runner`.

Flujo:

1. El backend valida usuario, permisos, plugin, límites y parámetros.
2. El backend crea una solicitud de ejecución durable.
3. `plugin-runner` recibe únicamente la especificación validada.
4. `plugin-runner` crea el contenedor efímero.
5. El contenedor ejecuta el código bajo restricciones.
6. `plugin-runner` recoge salida, errores y métricas.
7. El contenedor y el workspace temporal se eliminan.
8. El resultado y la auditoría se persisten.

El usuario no puede enviar opciones Docker arbitrarias.

## Alcance Foundation v1.0

Foundation v1.0 debe incluir:

- interfaz `PluginExecutionRuntime`;
- implementación `InProcessRuntime` limitada a plugins internos confiables;
- implementación funcional `DockerSandboxRuntime`;
- servicio interno `plugin-runner` o equivalente aislado;
- plugin demostrativo `python-restricted`;
- configuración de límites mediante variables de entorno e interfaz administrativa;
- validación estricta de comandos, imágenes, variables y mounts;
- logs y auditoría;
- tests unitarios e integración de aislamiento;
- documentación del modelo de amenazas.

## Criterios de aceptación

La fase no se considera terminada hasta comprobar que:

- un plugin no puede leer archivos arbitrarios del host;
- un plugin no puede acceder a secretos del backend;
- un plugin no puede ejecutar como root;
- un plugin no puede usar red sin permiso explícito;
- una ejecución que excede el timeout es cancelada;
- una ejecución que excede memoria o procesos falla de forma controlada;
- el contenedor se elimina después de éxito, error o cancelación;
- stdout, stderr y código de salida quedan registrados;
- todas las ejecuciones quedan asociadas a usuario, plugin, tarea y fecha;
- el backend principal no monta el socket Docker.

## Evolución futura

La interfaz debe permitir agregar posteriormente otros runtimes sin modificar el motor de plugins, por ejemplo:

- Kubernetes Jobs;
- gVisor;
- Firecracker;
- máquinas remotas;
- runners especializados por GPU.

Estas alternativas quedan fuera de Foundation v1.0.
