import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from pydantic import ValidationError

from app.api.instanews import _serialize_dispatch
from app.modules.instanews.schemas import InstaNewsSocialPublishRequest


def test_social_publish_requires_feed_and_story_images() -> None:
    payload = InstaNewsSocialPublishRequest(
        news_id="news-1",
        title="Noticia de prueba",
        caption="Texto editorial",
        feed_image_url="https://lh3.googleusercontent.com/d/feed=s2000",
        story_image_url="https://lh3.googleusercontent.com/d/story=s2000",
    )
    assert str(payload.feed_image_url).startswith("https://")
    assert str(payload.story_image_url).startswith("https://")


def test_social_publish_rejects_missing_story_image() -> None:
    with pytest.raises(ValidationError):
        InstaNewsSocialPublishRequest(
            news_id="news-1",
            title="Noticia de prueba",
            caption="Texto editorial",
            feed_image_url="https://lh3.googleusercontent.com/d/feed=s2000",
        )


@pytest.mark.asyncio
async def test_social_dispatch_refreshes_server_updated_timestamp() -> None:
    now = datetime.now(timezone.utc)
    dispatch = SimpleNamespace(
        facebook_publication_id=None,
        instagram_publication_id=None,
        facebook_story_publication_id=None,
        instagram_story_publication_id=None,
        status="queued",
        error=None,
        created_at=now,
        updated_at=now,
        news_id="news-1",
        attempts=1,
    )
    session = SimpleNamespace(flush=AsyncMock(), refresh=AsyncMock(), commit=AsyncMock())

    result = await _serialize_dispatch(session, dispatch)

    session.refresh.assert_awaited_once_with(dispatch)
    assert result["news_id"] == "news-1"
    assert result["updated_at"] == now.isoformat()
