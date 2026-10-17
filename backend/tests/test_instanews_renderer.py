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


def test_landscape_story_keeps_both_sides_of_source_photo() -> None:
    source = Image.new("RGB", (1600, 900), "#e62c27")
    source.paste(Image.new("RGB", (800, 900), "#1eaa5b"), (800, 0))
    original = BytesIO()
    source.save(original, "PNG")
    rendered, _ = render_social_asset(
        original.getvalue(), "Noticia de prueba", "Bajada breve de prueba.",
        "Municipales", OUTPUT_TEMPLATES["story"], "Río Grande",
    )
    with Image.open(BytesIO(rendered)) as image:
        left = image.getpixel((120, 500))
        right = image.getpixel((960, 500))
        assert left[0] > left[1] * 2
        assert right[1] > right[0] * 2


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


def test_senasa_source_adds_label_to_story_and_feed() -> None:
    source = BytesIO()
    Image.new("RGB", (1600, 1000), "#55788f").save(source, "JPEG")
    for template in OUTPUT_TEMPLATES.values():
        args = (source.getvalue(), "Novedades sanitarias", "Información de interés público.", "Nacionales", template, "Río Grande")
        ordinary, _ = render_social_asset(*args, "Gobierno TDF")
        senasa, _ = render_social_asset(*args, "SENASA COMUNICA")
        assert senasa != ordinary
        with Image.open(BytesIO(senasa)) as image:
            assert image.size == (template["width"], template["height"])


def test_legacy_judicial_category_renders_as_judiciales() -> None:
    source = BytesIO()
    Image.new("RGB", (1600, 1000), "#55788f").save(source, "JPEG")
    args = (source.getvalue(), "Resolución del tribunal", "Información del expediente.")
    for template in OUTPUT_TEMPLATES.values():
        old, _ = render_social_asset(*args, "Judicial", template)
        canonical, _ = render_social_asset(*args, "Judiciales", template)
        assert old == canonical
