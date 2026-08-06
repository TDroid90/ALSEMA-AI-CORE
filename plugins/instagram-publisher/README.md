# Instagram Publisher

Plugin genérico para configurar múltiples cuentas y preparar publicaciones de imagen mediante Instagram API with Instagram Login.

El plugin crea y supervisa el contenedor como una tarea durable. Cuando Instagram informa `FINISHED`, la publicación queda en estado `ready`. El endpoint `media_publish` solo se invoca después de una segunda solicitud autenticada con `confirmed: true`.

Permisos de Meta esperados:

- `instagram_business_basic`
- `instagram_business_content_publish`

La imagen debe estar disponible desde una URL HTTPS pública. Meta no puede descargar archivos alojados en `localhost`, redes privadas ni rutas del equipo.

Los campos `app_secret` y `access_token` se cifran antes de persistir y nunca se devuelven por API. Configure `SECRET_ENCRYPTION_KEY` con una clave independiente y estable en producción. Si se omite en desarrollo, el Core deriva una clave separada desde `APP_SECRET_KEY` para mantener compatibilidad con instalaciones existentes.

## Procedimiento

1. Abra `Plugins → Instagram`.
2. Registre una cuenta con etiqueta, App ID, App Secret, Instagram User ID, token y versión de API.
3. Use **Probar conexión** y confirme el perfil devuelto.
4. Ingrese una URL HTTPS pública y un caption.
5. Cree el contenedor y espere el estado `ready`.
6. Revise cuenta, imagen y caption.
7. Use **Confirmar y publicar** únicamente cuando corresponda.

Endpoints:

- `GET /api/v1/plugins/instagram/accounts`
- `POST /api/v1/plugins/instagram/accounts`
- `PATCH /api/v1/plugins/instagram/accounts/{account_id}`
- `POST /api/v1/plugins/instagram/test-connection`
- `POST /api/v1/plugins/instagram/media/image`
- `GET /api/v1/plugins/instagram/media`
- `GET /api/v1/plugins/instagram/media/{container_id}/status`
- `POST /api/v1/plugins/instagram/media/{container_id}/publish`

No se incluyen credenciales ni datos de marcas en el repositorio.
