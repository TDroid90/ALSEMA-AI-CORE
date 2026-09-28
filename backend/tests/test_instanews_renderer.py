from io import BytesIO

from PIL import Image

from app.modules.instanews.renderer import render_social_asset
from app.modules.instanews.templates import OUTPUT_TEMPLATES


def test_instanews_templates_render_exact_social_sizes() -> None:
    source = BytesIO()
    Image.new("RGB", (1600, 1000), "#55788f").save(source, "JPEG")
    for output, template in OUTPUT_TEMPLATES.items():
        rendered, fit = render_social_asset(
            source.getvalue(),
            "La Provincia presentó una política pública para Tierra del Fuego",
            "La iniciativa reúne a autoridades y organizaciones locales con una agenda de trabajo común.",
            "Gobierno",
            template,
            "San Sebastián",
        )
        with Image.open(BytesIO(rendered)) as image:
            assert image.size == (template["width"], template["height"]), output
            assert image.format == "PNG"
        assert fit["title_lines"] <= template["content"]["title_lines"]
        assert fit["summary_lines"] <= template["content"]["summary_lines"]


def test_article_link_is_never_rendered() -> None:
    source = BytesIO()
    Image.new("RGB", (1600, 1000), "#55788f").save(source, "JPEG")
    arguments = (
        source.getvalue(),
        "Título periodístico de prueba",
        "Bajada informativa sin superponer elementos.",
        "Ciudad",
    )
    article_url = "https://instanews.news/noticias/titulo-periodistico-de-prueba"

    story, _ = render_social_asset(*arguments, OUTPUT_TEMPLATES["story"], "Río Grande")
    feed, _ = render_social_asset(*arguments, OUTPUT_TEMPLATES["feed_4_5"], "Río Grande")

    assert article_url.encode() not in story
    assert article_url.encode() not in feed
