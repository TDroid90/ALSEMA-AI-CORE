import json

import httpx
import pytest
from pydantic import ValidationError

from app.api.instagram import InstagramImageCreate
from app.config.settings import Settings
from app.modules.plugins.instagram import (
    InstagramAPIError,
    InstagramCredentials,
    InstagramPublisherPlugin,
    sanitize_instagram_payload,
)
from app.shared.secrets import SecretCipher


def credentials() -> InstagramCredentials:
    return InstagramCredentials(
        app_id="123456",
        app_secret="test-app-secret",
        instagram_user_id="17841400000000000",
        access_token="test-access-token",
        api_version="v23.0",
    )


@pytest.mark.asyncio
async def test_connection_returns_profile_without_exposing_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v23.0/17841400000000000"
        assert request.url.params["fields"] == "id,username,account_type"
        assert request.headers["authorization"] == "Bearer test-access-token"
        assert "access_token" not in str(request.url)
        return httpx.Response(
            200,
            json={"id": "17841400000000000", "username": "test_account", "account_type": "BUSINESS"},
        )

    result = await InstagramPublisherPlugin(transport=httpx.MockTransport(handler)).test_connection(credentials())

    assert result == {
        "id": "17841400000000000",
        "username": "test_account",
        "account_type": "BUSINESS",
        "connection_status": "connected",
    }
    assert "test-access-token" not in json.dumps(result)


@pytest.mark.asyncio
async def test_meta_error_is_sanitized() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": "Invalid token test-access-token", "access_token": "test-access-token", "code": 190}},
        )

    with pytest.raises(InstagramAPIError) as raised:
        await InstagramPublisherPlugin(transport=httpx.MockTransport(handler)).test_connection(credentials())

    assert "test-access-token" not in str(raised.value)
    assert raised.value.details["access_token"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_container_integration_stops_before_publish() -> None:
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/media"):
            payload = json.loads(request.content.decode("utf-8"))
            assert payload == {
                "image_url": "https://images.example.com/test.jpg",
                "caption": "Información técnica: acción y publicación 🎙️",
            }
            assert request.headers["content-type"] == "application/json; charset=utf-8"
            return httpx.Response(200, json={"id": "container-123"})
        if request.url.path.endswith("/container-123"):
            return httpx.Response(200, json={"status_code": "FINISHED", "status": "Finished"})
        pytest.fail(f"Llamada inesperada: {request.url.path}")

    plugin = InstagramPublisherPlugin(transport=httpx.MockTransport(handler))
    created = await plugin.create_image_container(
        credentials(),
        "https://images.example.com/test.jpg",
        "Información técnica: acción y publicación 🎙️",
    )
    state = await plugin.get_container_status(credentials(), str(created["id"]))

    assert state["status_code"] == "FINISHED"
    assert calls == [
        "/v23.0/17841400000000000/media",
        "/v23.0/container-123",
    ]
    assert not any(path.endswith("/media_publish") for path in calls)


@pytest.mark.asyncio
async def test_story_container_uses_stories_media_type() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["media_type"] == "STORIES"
        assert payload["caption"] == "Última información desde Río Grande"
        return httpx.Response(200, json={"id": "story-container"})

    result = await InstagramPublisherPlugin(
        transport=httpx.MockTransport(handler)
    ).create_image_container(
        credentials(),
        "https://images.example.com/story.jpg",
        "Última información desde Río Grande",
        "story",
    )

    assert result["id"] == "story-container"


def test_secret_cipher_encrypts_at_rest() -> None:
    settings = Settings(
        app_secret_key="test-app-key-with-sufficient-length",
        secret_encryption_key="independent-test-encryption-key",
        database_url="postgresql+asyncpg://test:test@localhost/test",
        redis_url="redis://localhost:6379/15",
        ollama_base_url="http://localhost:11434",
    )
    cipher = SecretCipher(settings)
    encrypted = cipher.encrypt("sensitive-token")

    assert "sensitive-token" not in encrypted
    assert cipher.decrypt(encrypted) == "sensitive-token"


def test_image_requires_public_https_url() -> None:
    with pytest.raises(ValidationError):
        InstagramImageCreate(
            account_id="11111111-1111-1111-1111-111111111111",
            image_url="http://localhost/image.jpg",
            caption="Prueba",
        )


def test_recursive_sanitizer_redacts_secret_fields_and_values() -> None:
    result = sanitize_instagram_payload(
        {"access_token": "token-value", "nested": {"message": "failed token-value"}},
        ("token-value",),
    )
    assert result == {
        "access_token": "[REDACTED]",
        "nested": {"message": "failed [REDACTED]"},
    }
