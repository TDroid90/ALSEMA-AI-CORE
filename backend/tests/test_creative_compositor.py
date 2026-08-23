import json
from pathlib import Path

from PIL import Image, ImageDraw

from app.modules.creative.compositor import manifest_bytes, render_creative
from app.modules.creative.schemas import CreativeContent


def _rgba_product(path: Path) -> None:
    image = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
    ImageDraw.Draw(image).rounded_rectangle((80, 50, 420, 450), 40, fill=(25, 90, 160, 255))
    image.save(path)


def _logo(path: Path) -> None:
    image = Image.new("RGBA", (220, 80), (255, 255, 255, 0))
    ImageDraw.Draw(image).rectangle((5, 5, 215, 75), fill=(0, 194, 255, 255))
    image.save(path)


def test_compositor_generates_three_real_1080x1350_assets(tmp_path: Path) -> None:
    product, logo = tmp_path / "product.png", tmp_path / "logo.png"
    _rgba_product(product)
    _logo(logo)
    content = CreativeContent(
        id="CH-TEST",
        brand="cometag",
        title="Auriculares inalámbricos",
        description="Audio envolvente.",
        specs=["Bluetooth 5.3", "Micrófono integrado", "Batería extendida"],
        cta="Ver producto",
    )
    hashes: set[str] = set()
    for variant in ("A", "B", "C"):
        rendered = render_creative(content, variant, "instagram_feed", product, logo_path=logo)
        assert (rendered.width, rendered.height) == (1080, 1350)
        assert rendered.png.startswith(b"\x89PNG")
        assert rendered.manifest["qa"] == {"valid": True, "errors": [], "approval": "pending"}
        hashes.add(rendered.manifest["output_hash"])
        assert json.loads(manifest_bytes(rendered.manifest))["variant"] == variant
    assert len(hashes) == 3
