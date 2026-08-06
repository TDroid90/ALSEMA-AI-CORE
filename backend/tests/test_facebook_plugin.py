import json

import httpx
import pytest
from pydantic import ValidationError

from app.api.facebook import FacebookImageCreate
from app.modules.plugins.facebook import (
    FacebookAPIError,
    FacebookCredentials,
    FacebookPublisherPlugin,
    sanitize_facebook_payload,
)


def credentials() -> FacebookCredentials:
    return FacebookCredentials(
        app_id="123456",
        app_secret="test-app-secret",
        page_id="123450000000000",
        page_access_token="test-page-token",
        api_version="v26.0",
    )


@pytest.mark.asyncio
async def test_connection_returns_page_without_exposing_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v26.0/123450000000000"
        assert request.url.params["fields"] == "id,name,category,link"
        assert request.headers["authorization"] == "Bearer test-page-token"
        assert "test-page-token" not in str(request.url)
        return httpx.Response(200, json={"id": "123450000000000", "name": "Página editorial", "category": "News & media website", "link": "https://facebook.example/page"})

    result = await FacebookPublisherPlugin(
        transport=httpx.MockTransport(handler)
    ).test_connection(credentials())

    assert result["name"] == "Página editorial"
    assert result["connection_status"] == "connected"
    assert "test-page-token" not in json.dumps(result)


@pytest.mark.asyncio
async def test_feed_image_preserves_spanish_utf8() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        assert payload == {
            "url": "https://images.example.com/noticia.jpg",
            "caption": "Última información: economía, educación y acción 🇦🇷",
            "published": True,
        }
        assert request.headers["content-type"] == "application/json; charset=utf-8"
        return httpx.Response(200, json={"id": "photo-1", "post_id": "post-1"})

    result = await FacebookPublisherPlugin(
        transport=httpx.MockTransport(handler)
    ).publish_feed_image(
        credentials(),
        "https://images.example.com/noticia.jpg",
        "Última información: economía, educación y acción 🇦🇷",
    )

    assert result["post_id"] == "post-1"


@pytest.mark.asyncio
async def test_photo_story_uses_unpublished_photo_then_story_endpoint() -> None:
    calls: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        payload = json.loads(request.content.decode("utf-8"))
        if request.url.path.endswith("/photos"):
            assert payload["published"] is False
            return httpx.Response(200, json={"id": "photo-1"})
        if request.url.path.endswith("/photo_stories"):
            assert payload == {"photo_id": "photo-1"}
            return httpx.Response(200, json={"success": True, "post_id": "story-1"})
        pytest.fail(f"Llamada inesperada: {request.url.path}")

    plugin = FacebookPublisherPlugin(transport=httpx.MockTransport(handler))
    uploaded = await plugin.upload_story_photo(
        credentials(), "https://images.example.com/story.jpg", "Historia de prueba"
    )
    published = await plugin.publish_photo_story(credentials(), str(uploaded["id"]))

    assert published["post_id"] == "story-1"
    assert calls == [
        "/v26.0/123450000000000/photos",
        "/v26.0/123450000000000/photo_stories",
    ]


@pytest.mark.asyncio
async def test_meta_error_is_sanitized() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": {"message": "Invalid test-page-token", "access_token": "test-page-token"}})

    with pytest.raises(FacebookAPIError) as raised:
        await FacebookPublisherPlugin(
            transport=httpx.MockTransport(handler)
        ).test_connection(credentials())

    assert "test-page-token" not in str(raised.value)
    assert raised.value.details["access_token"] == "[REDACTED]"


def test_image_requires_public_https_url() -> None:
    with pytest.raises(ValidationError):
        FacebookImageCreate(
            account_id="11111111-1111-1111-1111-111111111111",
            image_url="http://localhost/image.jpg",
            caption="Prueba",
        )


def test_recursive_sanitizer_redacts_secrets() -> None:
    result = sanitize_facebook_payload(
        {"page_access_token": "token-value", "nested": {"message": "bad token-value"}},
        ("token-value",),
    )
    assert result == {
        "page_access_token": "[REDACTED]",
        "nested": {"message": "bad [REDACTED]"},
    }
