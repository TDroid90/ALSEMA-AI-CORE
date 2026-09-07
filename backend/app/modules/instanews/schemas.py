from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

SocialOutput = Literal["story", "feed_4_5"]


class InstaNewsSocialAssetRequest(BaseModel):
    news_id: str = Field(min_length=1, max_length=180)
    title: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1, max_length=2000)
    category: str = Field(default="Actualidad", max_length=120)
    source: str = Field(default="INSTANEWS", max_length=180)
    image_url: HttpUrl
    article_url: HttpUrl
    outputs: list[SocialOutput] = Field(min_length=1, max_length=2)


class InstaNewsRenderedAsset(BaseModel):
    output: SocialOutput
    content_base64: str
    content_type: Literal["image/png"] = "image/png"
    width: int
    height: int
    template_id: str
    template_version: str
    text_fit: dict[str, int | bool]
