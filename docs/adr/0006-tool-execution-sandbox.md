# ADR-0006: Política de sandbox para ejecución de herramientas

- Estado: Aceptado
- Fecha: 2026-08-04

## Contexto

El Core permitirá herramientas que leen archivos, realizan solicitudes HTTP y, en etapas posteriores, ejecutan Python o comandos. Estas capacidades pueden producir pérdida de datos, fuga de secretos o ejecución arbitraria si se exponen directamente al proceso principal.

El Foundation Build necesita herramientas funcionales, pero no debe convertir al servidor en un shell remoto sin límites.

## Decisión

Toda herramienta se ejecutará mediante un **Tool Executor** separado del agente y gobernado por políticas. Las herramientas de ejecución de código o shell deberán operar dentro de un entorno aislado y efímero.

Para el Foundation Build:

- `http_request` se limita por allowlist, timeout, tamaño y métodos permitidos.
- `read_file` y `write_file` operan únicamente dentro de workspaces montados y autorizados.
- No se permite acceso arbitrario al sistema de archivos del host.
- La ejecución Python, si se incluye, se realiza en un contenedor efímero sin privilegios, con red deshabilitada por defecto.
- La ejecución shell general queda fuera del alcance inicial, salvo comandos internos estáticos y expresamente registrados.
- Las herramientas no pueden acceder al socket Docker.
- Las credenciales se inyectan por referencia y nunca se exponen al modelo.

## Controles obligatorios

- Usuario no root.
- Filesystem de solo lectura salvo directorio temporal autorizado.
- Límites de CPU, RAM, tiempo y tamaño de salida.
- Red deshabilitada por defecto.
- Lista explícita de capacidades.
- Validación de entrada y salida.
- Auditoría con correlation ID.
- Eliminación del entorno temporal al finalizar.
- Cancelación forzada al superar timeout.
- Aprobación humana según nivel de riesgo.

## Consecuencias

### Positivas

- Reduce el impacto de prompts maliciosos o errores del agente.
- Separa capacidades de negocio de privilegios del host.
- Permite ampliar herramientas sin cambiar el modelo de seguridad.

### Negativas

- Mayor complejidad operativa.
- Sobrecosto al crear entornos efímeros.
- Algunas herramientas requerirán permisos específicos y documentación adicional.

## Prohibiciones

- `shell=true` con entrada libre proveniente del modelo.
- Montar el directorio raíz del host.
- Ejecutar contenedores privilegiados.
- Registrar secretos o variables sensibles.
- Permitir red abierta sin política.
- Confiar en que el prompt del agente reemplaza el aislamiento técnico.

## Criterio de revisión

Toda ampliación de privilegios, acceso al host, red o persistencia requiere una evaluación de amenazas y un ADR adicional.