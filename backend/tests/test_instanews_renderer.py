from io import BytesIO

from PIL import Image

from app.modules.instanews.renderer import _cover, render_social_asset
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


def test_landscape_story_fades_photo_into_black_without_a_hard_edge() -> None:
    source = Image.new("RGB", (1600, 900), "#ffffff")
    original = BytesIO()
    source.save(original, "PNG")
    image = _cover(original.getvalue(), (1080, 1920))
    brightness = [image.getpixel((540, round(1920 * fraction)))[0] for fraction in (0.50, 0.60, 0.70, 0.80, 0.90)]
    assert brightness[0] == 255
    assert brightness[0] > brightness[1] > brightness[2] > brightness[3] > brightness[4]
    assert brightness[4] < 20


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
