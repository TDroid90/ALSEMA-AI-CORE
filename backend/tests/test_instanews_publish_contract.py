import pytest
from pydantic import ValidationError

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
