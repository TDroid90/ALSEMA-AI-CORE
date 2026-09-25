from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from app.modules.instanews.renderer import ASSETS, fit_text, render_social_asset
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
            "https://instanews.news/noticias/la-provincia-presento-una-politica-publica-para-tierra-del-fuego",
        )
        with Image.open(BytesIO(rendered)) as image:
            assert image.size == (template["width"], template["height"]), output
            assert image.format == "PNG"
        assert fit["title_lines"] <= template["content"]["title_lines"]
        assert fit["summary_lines"] <= template["content"]["summary_lines"]


def test_article_link_is_rendered_only_on_story() -> None:
    source = BytesIO()
    Image.new("RGB", (1600, 1000), "#55788f").save(source, "JPEG")
    arguments = (
        source.getvalue(),
        "Título periodístico de prueba",
        "Bajada informativa sin superponer elementos.",
        "Ciudad",
    )
    article_url = "https://instanews.news/noticias/titulo-periodistico-de-prueba"

    story_with_link, _ = render_social_asset(
        *arguments, OUTPUT_TEMPLATES["story"], "Río Grande", article_url
    )
    story_without_link, _ = render_social_asset(
        *arguments, OUTPUT_TEMPLATES["story"], "Río Grande", None
    )
    feed_with_link, _ = render_social_asset(
        *arguments, OUTPUT_TEMPLATES["feed_4_5"], "Río Grande", article_url
    )
    feed_without_link, _ = render_social_asset(
        *arguments, OUTPUT_TEMPLATES["feed_4_5"], "Río Grande", None
    )

    assert story_with_link != story_without_link
    assert feed_with_link == feed_without_link


def test_long_article_link_stays_inside_story_width() -> None:
    maximum_width = 920
    fitted = fit_text(
        "https://instanews.news/noticias/una-noticia-con-un-enlace-muy-largo-que-debe-respetar-los-margenes-de-la-historia",
        maximum_width,
        2,
        22,
        18,
        1.18,
        "medium",
    )
    draw = ImageDraw.Draw(Image.new("RGB", (1080, 200)))
    font = ImageFont.truetype(str(ASSETS / "Montserrat-Medium.otf"), fitted.font_size)
    assert len(fitted.lines) <= 2
    assert all(draw.textlength(line, font=font) <= maximum_width for line in fitted.lines)
