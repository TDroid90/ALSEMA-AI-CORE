from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

CreativeFormat = Literal["instagram_feed", "story", "square", "x_horizontal"]


class CreativeContent(BaseModel):
    id: str = Field(min_length=1, max_length=255)
    sku: str | None = Field(default=None, max_length=255)
    brand: str = Field(pattern=r"^[a-z0-9-]{2,80}$")
    content_type: str = "producto"
    campaign: str = "producto"
    category: str = ""
    subcategory: str = ""
    title: str = Field(min_length=1, max_length=500)
    short_title: str | None = Field(default=None, max_length=500)
    description: str = Field(default="", max_length=2000)
    specs: list[str] = Field(default_factory=list, max_length=5)
    image_url: str | None = None
    local_asset_key: str | None = None
    destination_url: str | None = None
    cta: str = Field(default="Ver producto", max_length=100)
    source: str = "manual"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("specs")
    @classmethod
    def strip_specs(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()][:5]


class CreateCreativeJob(BaseModel):
    brand: str = Field(pattern=r"^[a-z0-9-]{2,80}$")
    catalog_item_id: UUID | None = None
    content: CreativeContent | None = None
    campaign: str = Field(default="producto", max_length=80)
    template_keys: list[str] = Field(
        default_factory=lambda: ["A", "B", "C"], min_length=1, max_length=3
    )
    format: CreativeFormat = "instagram_feed"
    use_text_ai: bool = True
    use_visual_ai: bool = False
    image_index: int = Field(default=0, ge=0, le=2)

    @field_validator("template_keys")
    @classmethod
    def validate_templates(cls, value: list[str]) -> list[str]:
        allowed = {"A", "B", "C"}
        if any(key not in allowed and not key.startswith("template:") for key in value):
            raise ValueError("Plantilla desconocida")
        if len(set(value)) != len(value):
            raise ValueError("Las plantillas no pueden repetirse")
        return value


class CreativeDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str = Field(default="", max_length=1000)


class CreativeTemplateInput(BaseModel):
    key: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,120}$")
    name: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=1000)
    document: dict[str, Any]
    publish: bool = False


class CreativeImportRequest(BaseModel):
    source_path: str = Field(
        default="/data/creative/import-source", pattern=r"^/data/creative(?:/[a-zA-Z0-9._/-]+)?$"
    )


class GoogleSheetsCatalogSync(BaseModel):
    brand: str = Field(pattern=r"^[a-z0-9-]{2,80}$")
    sheet_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{20,120}$")
    gid: str = Field(default="0", pattern=r"^[0-9]{1,20}$")
