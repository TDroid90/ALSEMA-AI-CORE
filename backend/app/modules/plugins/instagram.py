from collections.abc import Mapping
from typing import Protocol

import httpx
from pydantic import BaseModel, Field

from app.modules.plugins.instagram_models import InstagramAccount
from app.shared.secrets import SecretCipher

INSTAGRAM_GRAPH_HOST = "https://graph.instagram.com"
SECRET_KEYS = {"access_token", "app_secret", "token", "client_secret"}


class InstagramCredentials(BaseModel):
    app_id: str
    app_secret: str
    instagram_user_id: str
    access_token: str
    api_version: str = Field(pattern=r"^v\d+\.\d+$")


class InstagramAPIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class InstagramPublisher(Protocol):
    async def test_connection(self, credentials: InstagramCredentials) -> dict[str, object]: ...
    async def create_image_container(self, credentials: InstagramCredentials, image_url: str, caption: str, placement: str = "feed") -> dict[str, object]: ...
    async def get_container_status(self, credentials: InstagramCredentials, container_id: str) -> dict[str, object]: ...
    async def publish_container(self, credentials: InstagramCredentials, container_id: str) -> dict[str, object]: ...


def sanitize_instagram_payload(value: object, secrets: tuple[str, ...] = ()) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if str(key).lower() in SECRET_KEYS else sanitize_instagram_payload(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_instagram_payload(item, secrets) for item in value]
    if isinstance(value, str):
        sanitized = value
        for secret in secrets:
            if secret:
                sanitized = sanitized.replace(secret, "[REDACTED]")
        return sanitized
    return value


class InstagramPublisherPlugin:
    metadata = {"id": "instagram-publisher", "version": "1.0.0"}

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None, timeout: float = 30.0) -> None:
        self._transport = transport
        self._timeout = timeout

    async def _request(
        self,
        method: str,
        credentials: InstagramCredentials,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        url = f"{INSTAGRAM_GRAPH_HOST}/{credentials.api_version}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {credentials.access_token}"}
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=self._timeout,
                follow_redirects=False,
            ) as client:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    json=payload,
                    headers={**headers, "Content-Type": "application/json; charset=utf-8"},
                )
        except httpx.HTTPError as exc:
            raise InstagramAPIError("No se pudo conectar con Instagram.") from exc
        try:
            body = response.json()
        except ValueError:
            body = {"message": "Instagram devolvió una respuesta no JSON."}
        safe_body = sanitize_instagram_payload(body, (credentials.access_token, credentials.app_secret))
        if not response.is_success:
            error = safe_body.get("error", safe_body) if isinstance(safe_body, dict) else {}
            message = error.get("message", "Instagram rechazó la solicitud.") if isinstance(error, dict) else "Instagram rechazó la solicitud."
            raise InstagramAPIError(str(message), status_code=response.status_code, details=error if isinstance(error, dict) else {})
        if not isinstance(safe_body, dict):
            raise InstagramAPIError("Instagram devolvió una respuesta inesperada.")
        return safe_body

    async def test_connection(self, credentials: InstagramCredentials) -> dict[str, object]:
        profile = await self._request(
            "GET",
            credentials,
            credentials.instagram_user_id,
            params={"fields": "id,username,account_type"},
        )
        return {
            "id": str(profile.get("id", credentials.instagram_user_id)),
            "username": str(profile.get("username", "")),
            "account_type": str(profile.get("account_type", "")),
            "connection_status": "connected",
        }

    async def create_image_container(
        self,
        credentials: InstagramCredentials,
        image_url: str,
        caption: str,
        placement: str = "feed",
    ) -> dict[str, object]:
        payload: dict[str, object] = {"image_url": image_url}
        if caption:
            payload["caption"] = caption
        if placement == "story":
            payload["media_type"] = "STORIES"
        return await self._request(
            "POST",
            credentials,
            f"{credentials.instagram_user_id}/media",
            payload=payload,
        )

    async def get_container_status(self, credentials: InstagramCredentials, container_id: str) -> dict[str, object]:
        return await self._request(
            "GET",
            credentials,
            container_id,
            params={"fields": "status_code,status"},
        )

    async def publish_container(self, credentials: InstagramCredentials, container_id: str) -> dict[str, object]:
        return await self._request(
            "POST",
            credentials,
            f"{credentials.instagram_user_id}/media_publish",
            payload={"creation_id": container_id},
        )


def credentials_for_account(account: InstagramAccount, cipher: SecretCipher | None = None) -> InstagramCredentials:
    secret_cipher = cipher or SecretCipher()
    return InstagramCredentials(
        app_id=account.app_id,
        app_secret=secret_cipher.decrypt(account.app_secret_encrypted),
        instagram_user_id=account.instagram_user_id,
        access_token=secret_cipher.decrypt(account.access_token_encrypted),
        api_version=account.api_version,
    )
