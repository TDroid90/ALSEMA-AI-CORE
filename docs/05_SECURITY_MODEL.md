# 05 — Security Model

## Objetivo

Definir el modelo de seguridad de ALSEMA AI CORE desde la primera versión. La seguridad no se agrega al final: condiciona la arquitectura, los contratos, la ejecución de herramientas, el almacenamiento de secretos y la exposición de APIs.

## Supuestos

- La primera instalación será local y administrada por una sola persona.
- Aun así, el sistema debe estar preparado para múltiples usuarios y clientes externos.
- Los agentes pueden ejecutar acciones con efectos reales.
- Los plugins pueden introducir riesgo.
- Las credenciales de proveedores y clientes deben tratarse como secretos.
- Las empresas futuras consumirán el Core mediante API keys o credenciales específicas.

## Objetivos de seguridad

1. Autenticar usuarios y clientes.
2. Autorizar cada acción según permisos.
3. Aislar secretos y datos por ámbito.
4. Evitar que modelos o prompts obtengan privilegios implícitos.
5. Registrar acciones administrativas y ejecuciones sensibles.
6. Reducir el impacto de plugins defectuosos o maliciosos.
7. Permitir revocación inmediata de sesiones y API keys.
8. Evitar exposición accidental de datos en logs.

## Identidades

### Usuario humano

Accede mediante email y contraseña. En futuras versiones podrán añadirse SSO y MFA.

### Cliente de API

Accede mediante API key con scopes explícitos.

### Worker

Se identifica con credenciales internas rotables y limitadas al procesamiento de tareas.

### Plugin

No posee identidad humana. Ejecuta bajo una identidad técnica y una lista de capacidades aprobadas.

### Agente

No es una identidad de seguridad autónoma. Siempre ejecuta en nombre de un usuario, cliente o tarea del sistema.

## Autenticación

### Sesiones web

- Access token JWT de corta duración.
- Refresh token aleatorio, rotado y almacenado mediante hash.
- Refresh tokens ligados a una sesión persistente.
- Cierre de sesión revoca la sesión.
- Cambio de contraseña puede revocar todas las sesiones.
- Cookies `HttpOnly`, `Secure` en producción y `SameSite=Lax` o más estricto.

### Contraseñas

- Hash Argon2id.
- Política mínima configurable.
- Nunca registrar contraseñas ni hashes.
- El administrador inicial se crea con variables de entorno durante el bootstrap.
- Después de la instalación, las credenciales se administran desde la interfaz.

### API keys

Formato recomendado:

`aas_<entorno>_<prefijo>_<secreto>`

- Solo se muestra completa una vez.
- Se almacena hash del secreto y prefijo visible.
- Incluye scopes, vencimiento y estado de revocación.
- Se registra último uso sin guardar el valor.
- Debe poder rotarse sin interrupción mediante coexistencia temporal.

## Autorización

Modelo RBAC con permisos atómicos.

Ejemplos:

- `conversations:read`
- `conversations:write`
- `agents:read`
- `agents:publish`
- `tools:execute:safe`
- `tools:execute:guarded`
- `workflows:run`
- `providers:manage`
- `plugins:manage`
- `users:manage`
- `system:admin`

Los endpoints verifican permisos en la capa de aplicación, no solo en la UI.

## Roles iniciales

### System Administrator

Acceso total. Debe existir al menos uno activo.

### Operator

Puede usar chats, ejecutar agentes y workflows aprobados, ver tareas y logs funcionales.

### Viewer

Acceso de lectura a recursos permitidos.

### API Client

No es un rol fijo: opera exclusivamente según scopes de su API key.

## Modelo de riesgo para herramientas

### Safe

Lectura o transformación sin efectos externos significativos.

Ejemplos:

- leer un archivo dentro del almacenamiento permitido;
- transformar texto;
- consultar estado del sistema.

Puede ejecutarse automáticamente si el agente tiene permiso.

### Guarded

Produce cambios limitados o consume recursos relevantes.

Ejemplos:

- escribir archivos;
- ejecutar solicitudes HTTP salientes;
- modificar datos del Core;
- lanzar trabajos largos.

Requiere permiso explícito y puede requerir confirmación según la política del agente.

### Dangerous

Puede afectar el host, secretos, datos críticos o sistemas externos.

Ejemplos:

- ejecutar shell arbitrario;
- borrar archivos;
- ejecutar código no confiable;
- publicar contenido externamente;
- modificar credenciales.

No se habilita por defecto en Foundation Build. Cuando exista, deberá usar sandbox, allowlists y confirmación humana obligatoria.

## Prompt injection y tool calling

- El contenido del usuario, archivos y páginas externas se considera no confiable.
- Las instrucciones recuperadas desde datos no pueden elevar privilegios.
- La selección de herramientas está limitada por la política del agente y el actor.
- El modelo propone llamadas; la aplicación valida schema, permiso, riesgo y límites antes de ejecutar.
- Los resultados de herramientas se etiquetan como datos, no instrucciones del sistema.
- Nunca se entregan secretos al modelo salvo que una integración lo requiera explícitamente y exista una política segura.

## Plugins

Cada plugin debe declarar en su manifest:

- nombre y versión;
- capacidades;
- herramientas registradas;
- endpoints opcionales;
- permisos requeridos;
- acceso de red requerido;
- acceso de almacenamiento requerido;
- variables secretas;
- healthcheck.

Reglas:

- Deshabilitados por defecto tras instalarse.
- Validación de manifest antes del registro.
- No acceden directamente a secretos de otros plugins.
- No pueden montar rutas arbitrarias del host.
- Sus errores no deben derribar el proceso principal.
- Toda ejecución queda correlacionada y auditable.

## Secretos

- Variables de entorno solo para bootstrap e infraestructura.
- Secretos administrados por la aplicación se cifran en reposo.
- Clave maestra fuera de la base de datos.
- Valores sensibles se redaccionan en API, logs y eventos.
- La UI muestra estado configurado/no configurado, nunca el secreto completo.
- Debe existir mecanismo de rotación.

## Red

Configuración por defecto:

- Frontend y API expuestos en localhost o red privada.
- PostgreSQL y Redis no se publican a Internet.
- CORS limitado a orígenes configurados.
- Rate limiting por usuario, API key e IP.
- Tamaño máximo de payload y archivos configurable.
- Timeouts explícitos para proveedores y herramientas.
- Las solicitudes salientes deben admitir allowlists futuras.

## Archivos

- Los adjuntos se almacenan con IDs internos.
- Nunca confiar en el nombre original como ruta.
- Normalizar MIME type y extensión.
- Límites de tamaño por configuración.
- Escaneo opcional futuro.
- Evitar path traversal.
- No servir archivos privados sin autorización.

## Logs y auditoría

### Logs operativos

Pueden contener identificadores, tiempos, estados y errores redaccionados.

### Audit events

Deben registrar:

- login y logout;
- creación/revocación de API keys;
- cambios de roles y permisos;
- cambios de proveedores;
- publicación de agentes y workflows;
- habilitación/deshabilitación de plugins;
- ejecuciones guarded o dangerous;
- cambios de configuración crítica.

Nunca registrar:

- contraseñas;
- tokens completos;
- API keys completas;
- cookies;
- prompts o contenidos sensibles sin una política explícita;
- secretos de plugins.

## Protección de datos

- Separación lógica por usuario y ámbito.
- Exportación y eliminación futura por usuario/proyecto.
- Retención configurable para mensajes, tareas y logs.
- Soft delete funcional y purga programada cuando corresponda.
- Memorias con procedencia y fecha de expiración.

## Bootstrap seguro

Variables mínimas:

- `AAS_ADMIN_EMAIL`
- `AAS_ADMIN_PASSWORD`
- `AAS_SECRET_KEY`
- `AAS_ENCRYPTION_KEY`

Proceso:

1. Arrancar infraestructura.
2. Aplicar migraciones.
3. Crear administrador si no existe.
4. Marcar instalación inicial completada.
5. No volver a recrear o sobrescribir credenciales.

La contraseña de bootstrap debe cambiarse desde la UI y puede impedirse el acceso normal hasta hacerlo.

## Respuesta ante incidentes

La plataforma debe permitir:

- revocar todas las sesiones;
- revocar una API key;
- deshabilitar un proveedor o plugin;
- cancelar tareas activas;
- consultar eventos correlacionados;
- exportar auditoría;
- activar modo mantenimiento.

## Criterios mínimos para Foundation Build

- Argon2id implementado.
- JWT y refresh rotation probados.
- RBAC aplicado en backend.
- API keys con hash, scopes y revocación.
- Cifrado de secretos de proveedores.
- Redacción de campos sensibles.
- Auditoría de acciones administrativas.
- Rate limiting básico.
- Validación de archivos.
- Herramientas clasificadas por riesgo.
- Ninguna ejecución de shell arbitrario habilitada.
