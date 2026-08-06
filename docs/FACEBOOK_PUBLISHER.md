# Facebook Publisher

## Alcance

`facebook-publisher` administra múltiples páginas de Facebook sin lógica específica de clientes. Publica imágenes con texto en el feed y fotos como historias mediante la API Graph oficial.

## Permisos y token

Cada cuenta necesita un token de acceso de Página perteneciente a una app de Meta con el caso de uso **Administrar todos los aspectos de tu página** y estos permisos:

- `pages_manage_posts`
- `pages_read_engagement`
- `pages_show_list`

La persona que autoriza debe poder realizar `CREATE_CONTENT` en la página. El token se cifra con `SECRET_ENCRYPTION_KEY`, no se incluye en URLs ni logs y no vuelve a mostrarse luego de guardarlo.

## Configuración

En `Plugins → Facebook` se registran:

- etiqueta de cuenta;
- App ID y App Secret;
- Facebook Page ID;
- Page Access Token;
- versión de API;
- estado;
- publicación automática o confirmación manual.

La publicación automática está desactivada por defecto. Se puede habilitar por cuenta para workflows previamente aprobados. La opción manual deja el contenido en `ready` y muestra **Confirmar y publicar**.

## Flujos

### Feed

1. ALSEMA valida URL HTTPS y texto UTF-8.
2. La tarea queda `ready` o continúa automáticamente según la cuenta.
3. La publicación llama a `POST /{page_id}/photos` con `url`, `caption` y `published=true`.

### Historia de foto

1. ALSEMA llama a `POST /{page_id}/photos` con `published=false`.
2. Conserva el `photo_id` y deja la tarea en `ready`.
3. Tras la confirmación o automáticamente, llama a `POST /{page_id}/photo_stories` con `photo_id`.

Estados durables: `queued`, `uploading`, `ready`, `publishing`, `published` y `failed`.

## API

```text
GET    /api/v1/plugins/facebook/accounts
POST   /api/v1/plugins/facebook/accounts
PATCH  /api/v1/plugins/facebook/accounts/{account_id}
POST   /api/v1/plugins/facebook/test-connection
POST   /api/v1/plugins/facebook/media/image
GET    /api/v1/plugins/facebook/media
POST   /api/v1/plugins/facebook/media/{publication_id}/publish
```

Todas las rutas requieren autenticación y `plugins:manage`.

## Texto y acentos

La UI envía JSON con `charset=utf-8`, el backend normaliza Unicode en NFC, PostgreSQL usa UTF-8 y las solicitudes a Meta usan JSON UTF-8. Las pruebas cubren tildes, `ñ` y emojis.
