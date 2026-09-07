import json

from sqlalchemy import select

from app.modules.creative.models import CreativeBrand, CreativeTemplate
from app.modules.instanews.templates import OUTPUT_TEMPLATES, editor_document
from app.shared.database import SessionFactory


async def bootstrap_instanews_templates() -> None:
    async with SessionFactory() as session:
        brand = await session.scalar(select(CreativeBrand).where(CreativeBrand.slug == "instanews"))
        if brand is None:
            session.add(
                CreativeBrand(
                    slug="instanews",
                    name="InstaNews",
                    profile_json=json.dumps(
                        {"primary": "#07111f", "accent": "#ffc107", "font": "Montserrat"}
                    ),
                )
            )
        for output, definition in OUTPUT_TEMPLATES.items():
            exists = await session.scalar(
                select(CreativeTemplate).where(CreativeTemplate.key == definition["key"])
            )
            if exists is None:
                session.add(
                    CreativeTemplate(
                        key=definition["key"],
                        name=definition["name"],
                        description="Plantilla periodística oficial migrada desde INSTANEWS.",
                        renderer="instanews",
                        document_json=json.dumps(editor_document(output), ensure_ascii=False),
                        version=1,
                        status="published",
                    )
                )
        await session.commit()
