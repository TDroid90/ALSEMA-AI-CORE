# Instagram Publisher

## Alcance

`instagram-publisher` es una integración genérica con Instagram API with Instagram Login. No contiene nombres, prompts ni reglas de ninguna empresa. Una instalación puede registrar varias cuentas y elegir la cuenta destino para cada contenedor.

Host autorizado: `https://graph.instagram.com`.

Permisos esperados en el token:

- `instagram_business_basic`
- `instagram_business_content_publish`

## Configuración

La configuración principal se realiza en `Plugins → Instagram`. Cada cuenta contiene etiqueta, App ID, App Secret, Instagram User ID, Access Token, versión de API y estado.

`app_secret` y `access_token` se cifran antes de escribirse en PostgreSQL. Las lecturas de API solo indican si están configurados y nunca devuelven sus valores. La clave recomendada es:

```text
SECRET_ENCRYPTION_KEY=<valor aleatorio largo, estable e independiente>
```

En desarrollo, si no existe esa variable, el Core deriva una clave separada desde `APP_SECRET_KEY`. Cambiar cualquiera de estas claves sin recifrar los secretos impedirá descifrarlos.

Bootstrap opcional para una primera cuenta:

```text
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_USER_ID=
INSTAGRAM_API_VERSION=v23.0
INSTAGRAM_ACCOUNT_LABEL=Development Instagram
```

Los cuatro campos de credenciales deben estar completos o todos vacíos. Las cuentas adicionales se registran desde la UI.

## Flujo seguro

1. El usuario valida una URL HTTPS pública y un caption.
2. La API crea una publicación durable y una tarea ARQ en estado `queued`.
3. El worker cambia a `uploading` y llama a `POST /{ig_user_id}/media`.
4. El worker consulta `GET /{container_id}?fields=status_code,status` mientras el estado es `processing`.
5. Al recibir `FINISHED`, la publicación queda `ready` y el worker se detiene.
6. La UI muestra cuenta, imagen, caption, contenedor y estado.
7. Una persona confirma expresamente la publicación.
8. El backend exige `{ "confirmed": true }`, crea otra tarea y recién entonces llama a `POST /{ig_user_id}/media_publish`.

```text
queued → uploading → processing → ready → publishing → published
                                           ↘ failed
```

La imagen debe ser descargable por Meta sin autenticación y mediante HTTPS. No se aceptan `localhost`, loopback ni hosts `.local`.

## API

```text
GET    /api/v1/plugins/instagram/accounts
POST   /api/v1/plugins/instagram/accounts
PATCH  /api/v1/plugins/instagram/accounts/{account_id}
POST   /api/v1/plugins/instagram/test-connection
POST   /api/v1/plugins/instagram/media/image
GET    /api/v1/plugins/instagram/media
GET    /api/v1/plugins/instagram/media/{container_id}/status
POST   /api/v1/plugins/instagram/media/{container_id}/publish
```

Todas las rutas requieren autenticación y `plugins:manage`. `media_publish` exige una segunda solicitud con `{ "confirmed": true }`.

## Pruebas

Las pruebas automáticas usan una API simulada y cubren perfil, redacción, cifrado, validación HTTPS, creación y estado del contenedor, y ausencia de llamadas a `media_publish` durante la preparación.

La prueba real operativa debe detenerse en `ready`. `media_id` y `published_at` deben seguir vacíos hasta la aprobación manual.
