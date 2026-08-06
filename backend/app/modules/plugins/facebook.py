from collections.abc import Mapping
from typing import Protocol

import httpx
from pydantic import BaseModel, Field

from app.modules.plugins.facebook_models import FacebookAccount
from app.shared.secrets import SecretCipher

FACEBOOK_GRAPH_HOST = "https://graph.facebook.com"
SECRET_KEYS = {"access_token", "page_access_token", "app_secret", "token", "client_secret"}


class FacebookCredentials(BaseModel):
    app_id: str
    app_secret: str
    page_id: str
    page_access_token: str
    api_version: str = Field(pattern=r"^v\d+\.\d+$")


class FacebookAPIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class FacebookPublisher(Protocol):
    async def test_connection(self, credentials: FacebookCredentials) -> dict[str, object]: ...
    async def publish_feed_image(self, credentials: FacebookCredentials, image_url: str, caption: str) -> dict[str, object]: ...
    async def upload_story_photo(self, credentials: FacebookCredentials, image_url: str, caption: str) -> dict[str, object]: ...
    async def publish_photo_story(self, credentials: FacebookCredentials, photo_id: str) -> dict[str, object]: ...


def sanitize_facebook_payload(value: object, secrets: tuple[str, ...] = ()) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if str(key).lower() in SECRET_KEYS else sanitize_facebook_payload(item, secrets)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_facebook_payload(item, secrets) for item in value]
    if isinstance(value, str):
        sanitized = value
        for secret in secrets:
            if secret:
                sanitized = sanitized.replace(secret, "[REDACTED]")
        return sanitized
    return value


class FacebookPublisherPlugin:
    metadata = {"id": "facebook-publisher", "version": "1.0.0"}

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None, timeout: float = 30.0) -> None:
        self._transport = transport
        self._timeout = timeout

    async def _request(
        self,
        method: str,
        credentials: FacebookCredentials,
        path: str,
        *,
        params: dict[str, str] | None = None,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        url = f"{FACEBOOK_GRAPH_HOST}/{credentials.api_version}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {credentials.page_access_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        try:
            async with httpx.AsyncClient(transport=self._transport, timeout=self._timeout, follow_redirects=False) as client:
                response = await client.request(method, url, params=params, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise FacebookAPIError("No se pudo conectar con Facebook.") from exc
        try:
            body = response.json()
        except ValueError:
            body = {"message": "Facebook devolvió una respuesta no JSON."}
        safe_body = sanitize_facebook_payload(body, (credentials.page_access_token, credentials.app_secret))
        if not response.is_success:
            error = safe_body.get("error", safe_body) if isinstance(safe_body, dict) else {}
            message = error.get("message", "Facebook rechazó la solicitud.") if isinstance(error, dict) else "Facebook rechazó la solicitud."
            raise FacebookAPIError(str(message), status_code=response.status_code, details=error if isinstance(error, dict) else {})
        if not isinstance(safe_body, dict):
            raise FacebookAPIError("Facebook devolvió una respuesta inesperada.")
        return safe_body

    async def test_connection(self, credentials: FacebookCredentials) -> dict[str, object]:
        profile = await self._request(
            "GET",
            credentials,
            credentials.page_id,
            params={"fields": "id,name,category,link"},
        )
        return {
            "id": str(profile.get("id", credentials.page_id)),
            "name": str(profile.get("name", "")),
            "category": str(profile.get("category", "")),
            "link": str(profile.get("link", "")),
            "connection_status": "connected",
        }

    async def publish_feed_image(self, credentials: FacebookCredentials, image_url: str, caption: str) -> dict[str, object]:
        return await self._request(
            "POST",
            credentials,
            f"{credentials.page_id}/photos",
            payload={"url": image_url, "caption": caption, "published": True},
        )

    async def upload_story_photo(self, credentials: FacebookCredentials, image_url: str, caption: str) -> dict[str, object]:
        return await self._request(
            "POST",
            credentials,
            f"{credentials.page_id}/photos",
            payload={"url": image_url, "caption": caption, "published": False},
        )

    async def publish_photo_story(self, credentials: FacebookCredentials, photo_id: str) -> dict[str, object]:
        return await self._request(
            "POST",
            credentials,
            f"{credentials.page_id}/photo_stories",
            payload={"photo_id": photo_id},
        )


def credentials_for_facebook_account(account: FacebookAccount, cipher: SecretCipher | None = None) -> FacebookCredentials:
    secret_cipher = cipher or SecretCipher()
    return FacebookCredentials(
        app_id=account.app_id,
        app_secret=secret_cipher.decrypt(account.app_secret_encrypted),
        page_id=account.page_id,
        page_access_token=secret_cipher.decrypt(account.page_access_token_encrypted),
        api_version=account.api_version,
    )
