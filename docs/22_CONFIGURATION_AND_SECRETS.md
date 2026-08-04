# 22 — Configuration and Secrets

## Propósito

Definir una configuración segura, validada y operable desde entorno local sin requerir edición manual constante de archivos internos.

## Fuentes de configuración

Orden de precedencia:

1. Valores por defecto seguros.
2. Archivo `.env` local no versionado.
3. Variables de entorno.
4. Configuración persistente administrable desde UI.
5. Parámetros explícitos de ejecución cuando estén permitidos.

Los secretos no deben guardarse en la misma tabla que la configuración común.

## Categorías

### Estática de arranque

Requiere reinicio:

- conexión PostgreSQL;
- conexión Redis;
- secret key principal;
- puertos;
- modo de entorno;
- almacenamiento;
- administrador inicial.

### Dinámica

Puede cambiarse desde UI:

- límites de tareas;
- concurrencia por proveedor;
- preferencias de modelos;
- políticas de retención;
- timeouts permitidos;
- configuración no secreta de plugins.

### Secreta

- API keys;
- tokens OAuth;
- claves privadas;
- credenciales externas;
- secretos de firma.

## Validación

- Configuración tipada con Pydantic Settings.
- Fallar rápido ante valores obligatorios inválidos.
- Mensajes de error claros sin imprimir secretos.
- Validar rangos, URLs, formatos y dependencias entre campos.
- La UI debe reutilizar esquemas equivalentes.

## Almacenamiento de secretos

v1 debe usar cifrado en reposo mediante una clave maestra provista por entorno.

Reglas:

- Nunca devolver el valor completo después de guardarlo.
- Mostrar solo estado o últimos caracteres cuando sea seguro.
- Permitir reemplazo y revocación.
- Registrar auditoría sin valor secreto.
- No incluir secretos en exports generales.
- No registrar secretos en logs o errores.

## Rotación

Debe documentarse cómo rotar:

- JWT signing secret;
- clave maestra de cifrado;
- API keys internas;
- credenciales de proveedor.

La rotación de la clave maestra requiere proceso controlado de recifrado.

## `.env.example`

Debe:

- contener todas las variables admitidas;
- explicar cada una;
- usar valores ficticios;
- marcar obligatorias y opcionales;
- incluir recomendaciones de generación segura;
- no incluir credenciales funcionales.

## UI de configuración

- Agrupación por módulo.
- Búsqueda.
- Validación previa.
- Indicación de reinicio requerido.
- Historial de cambios administrativos.
- Restablecer valores no secretos a defaults.
- Confirmación para cambios de alto impacto.

## Exportación e importación

La configuración no secreta puede exportarse en formato versionado.

La importación:

- valida versión;
- muestra diff;
- no sobrescribe secretos;
- requiere aprobación;
- registra auditoría.

## Criterios de aceptación

- Arranque falla claramente con configuración inválida.
- Secretos no aparecen en API, UI o logs.
- Configuración dinámica persiste.
- Cambios que requieren reinicio se identifican.
- Existe auditoría de cambios.
- `.env.example` permite una instalación limpia.
