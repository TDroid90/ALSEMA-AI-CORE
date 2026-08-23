from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

from app.modules.creative.policy import validate_creative_policy
from app.modules.creative.schemas import CreativeContent

FORMATS: dict[str, tuple[int, int]] = {
    "instagram_feed": (1080, 1350),
    "story": (1080, 1920),
    "square": (1080, 1080),
    "x_horizontal": (1600, 900),
}


@dataclass(frozen=True)
class RenderedCreative:
    png: bytes
    manifest: dict[str, Any]
    width: int
    height: int


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def _wrap(
    draw: ImageDraw.ImageDraw, text: str, width: int, max_lines: int, start: int
) -> tuple[list[str], ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    for size in range(start, 23, -2):
        face = _font(size, True)
        lines: list[str] = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if not current or draw.textbbox((0, 0), candidate, font=face)[2] <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        if len(lines) <= max_lines:
            return lines, face
    return lines[:max_lines], _font(24, True)


def _transparent_image(path: Path) -> Image.Image:
    if not path.exists():
        raise ValueError("esta foto necesita recorte: el archivo no existe")
    image = Image.open(path).convert("RGBA")
    if image.getchannel("A").getextrema()[0] == 255:
        sibling = path.with_name(f"{path.stem}.cutout.png")
        if sibling.exists():
            image = Image.open(sibling).convert("RGBA")
    if image.getchannel("A").getextrema()[0] == 255:
        raise ValueError("esta foto necesita recorte: no hay un recorte transparente")
    return image


def _features(specs: list[str]) -> list[str]:
    blocked = re.compile(r"^(?:sku|id|ean|upc|gtin|mpn|c[oó]digo|referencia)\s*:", re.IGNORECASE)
    result: list[str] = []
    for value in specs:
        for part in re.split(r"\s*[;|·]\s*", value):
            clean = re.sub(r"\s+", " ", part).strip(" .")
            if not clean or blocked.match(clean):
                continue
            clean = re.sub(r"^[^:]{1,48}:\s*", "", clean).strip()
            if clean and clean.casefold() not in {item.casefold() for item in result}:
                result.append(clean)
    return result[:5]


def _campaign(content: CreativeContent) -> tuple[str, tuple[int, int, int, int]]:
    if content.campaign.casefold() == "preventa":
        return "PREVENTA", (194, 99, 145, 255)
    if content.campaign.casefold() in {"nuevo_ingreso", "nuevo ingreso"}:
        return "NUEVO INGRESO", (139, 180, 102, 255)
    return (content.category or "PRODUCTO").upper(), (0, 184, 217, 255)


def _background(size: tuple[int, int], variant: str, background: Path | None) -> Image.Image:
    if background and background.exists():
        return ImageOps.fit(Image.open(background).convert("RGBA"), size, Image.Resampling.LANCZOS)
    base = {
        "A": (8, 15, 28, 255),
        "B": (12, 12, 18, 255),
        "C": (226, 232, 235, 255),
    }.get(variant, (8, 15, 28, 255))
    image = Image.new("RGBA", size, base)
    draw = ImageDraw.Draw(image)
    accent = (0, 184, 217, 52) if variant != "C" else (18, 54, 64, 25)
    for offset in range(-size[1], size[0], 90):
        draw.line((offset, 0, offset + size[1], size[1]), fill=accent, width=1)
    return image


def _place_product(
    canvas: Image.Image, cutout: Image.Image, variant: str, content: CreativeContent
) -> None:
    width, height = canvas.size
    layout = content.metadata.get("layout", {}) if isinstance(content.metadata, dict) else {}
    x = float(layout.get("productX", 50 if variant != "B" else 68))
    y = float(layout.get("productY", 30))
    scale = max(0.45, min(1.35, float(layout.get("productScale", 1.0))))
    maximum = (int(width * (0.63 if variant != "B" else 0.55) * scale), int(height * 0.48 * scale))
    product = cutout.copy()
    product.thumbnail(maximum, Image.Resampling.LANCZOS)
    px = max(0, min(width - product.width, int(width * x / 100 - product.width / 2)))
    py = max(
        0, min(int(height * 0.57) - product.height, int(height * y / 100 - product.height / 2))
    )
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    mask = product.getchannel("A").filter(ImageFilter.GaussianBlur(22))
    shadow.paste((0, 0, 0, 115), (px + 18, py + 26), mask)
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(product, (px, py))


def _draw_logo(canvas: Image.Image, logo: Path | None, variant: str) -> bool:
    if logo is None or not logo.exists():
        return False
    width, _ = canvas.size
    image = Image.open(logo).convert("RGBA")
    image.thumbnail((155, 96), Image.Resampling.LANCZOS)
    if variant == "C":
        badge = Image.new("RGBA", (image.width + 28, image.height + 24), (255, 255, 255, 230))
        badge.alpha_composite(image, (14, 12))
        canvas.alpha_composite(badge, (width - badge.width - 52, 44))
    else:
        canvas.alpha_composite(image, (width - image.width - 58, 50))
    return True


def _draw_copy(canvas: Image.Image, content: CreativeContent, variant: str) -> None:
    width, height = canvas.size
    draw = ImageDraw.Draw(canvas)
    label, accent = _campaign(content)
    title = (content.short_title or content.title).upper()
    features = _features(content.specs)
    if variant == "C":
        text = (25, 44, 52, 255)
        muted = (73, 91, 98, 255)
        panel_top = int(height * 0.56)
        draw.rectangle((0, panel_top, width, height), fill=(245, 247, 248, 245))
        draw.text((70, panel_top + 52), label, font=_font(24, True), fill=(12, 107, 125, 255))
        lines, face = _wrap(draw, title, width - 140, 3, 64)
        y = panel_top + 104
        for line in lines:
            draw.text((70, y), line, font=face, fill=text)
            y += int(getattr(face, "size", 32) * 1.08)
        for index, feature in enumerate(features[:3]):
            draw.text((72, y + 26 + index * 42), f"—  {feature}", font=_font(19, False), fill=muted)
        button_y = min(height - 142, y + 28 + max(1, len(features[:3])) * 42)
        draw.rounded_rectangle((70, button_y, 350, button_y + 62), 8, fill=(12, 107, 125, 255))
        draw.text((112, button_y + 16), content.cta, font=_font(24, True), fill="white")
        return
    panel_top = int(height * 0.56)
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle((0, panel_top, width, height), fill=(5, 10, 20, 224))
    canvas.alpha_composite(overlay)
    draw = ImageDraw.Draw(canvas)
    x = 68 if variant == "A" else 58
    if variant == "B":
        draw.polygon(
            [
                (0, panel_top),
                (int(width * 0.67), panel_top),
                (int(width * 0.52), height),
                (0, height),
            ],
            fill=(5, 10, 20, 245),
        )
    draw.rounded_rectangle((x, panel_top + 38, x + 310, panel_top + 91), 12, fill=accent)
    draw.text((x + 18, panel_top + 50), label, font=_font(23, True), fill=(5, 12, 24, 255))
    max_width = int(width * (0.56 if variant == "B" else 0.86))
    lines, face = _wrap(draw, title, max_width, 3, 62)
    y = panel_top + 122
    for line in lines:
        draw.text((x, y), line, font=face, fill="white")
        y += int(getattr(face, "size", 32) * 1.08)
    if variant == "B":
        card_x = int(width * 0.64)
        draw.rounded_rectangle(
            (card_x, panel_top + 104, width - 58, panel_top + 365),
            16,
            fill=(15, 25, 39, 235),
            outline=accent,
            width=2,
        )
        for index, feature in enumerate(features):
            draw.text(
                (card_x + 22, panel_top + 134 + index * 43),
                f"{index + 1:02}  {feature}",
                font=_font(16, True),
                fill=(231, 239, 247, 255),
            )
    else:
        chips_y = y + 22
        chip_x = x
        for feature in features:
            text_width = draw.textbbox((0, 0), feature, font=_font(16, True))[2]
            chip_width = int(min(230, text_width + 26))
            if chip_x + chip_width > width - 60:
                chip_x = x
                chips_y += 39
            draw.rounded_rectangle(
                (chip_x, chips_y, chip_x + chip_width, chips_y + 31),
                8,
                fill=(17, 30, 47, 255),
                outline=accent,
                width=1,
            )
            draw.text(
                (chip_x + 12, chips_y + 6), feature, font=_font(16, True), fill=(230, 239, 247, 255)
            )
            chip_x += chip_width + 9
    button_y = height - 150
    draw.rounded_rectangle((x, button_y, x + 310, button_y + 62), 14, fill=accent)
    draw.text((x + 54, button_y + 16), content.cta, font=_font(24, True), fill=(5, 12, 24, 255))


def _color(value: str, opacity: float = 1) -> tuple[int, int, int, int]:
    try:
        rgb = ImageColor.getrgb(value)
    except ValueError:
        rgb = (0, 0, 0)
    return (*rgb[:3], max(0, min(255, round(255 * opacity))))


def _render_layer_document(
    canvas: Image.Image, document: dict[str, Any], content: CreativeContent
) -> None:
    source_width = max(1, int(document.get("width", canvas.width)))
    source_height = max(1, int(document.get("height", canvas.height)))
    sx, sy = canvas.width / source_width, canvas.height / source_height
    draw = ImageDraw.Draw(canvas)
    for layer in sorted(document.get("layers", []), key=lambda item: item.get("z", 0)):
        if not layer.get("visible", True):
            continue
        x, y = round(float(layer.get("x", 0)) * sx), round(float(layer.get("y", 0)) * sy)
        width, height = (
            max(1, round(float(layer.get("width", 1)) * sx)),
            max(1, round(float(layer.get("height", 1)) * sy)),
        )
        opacity = float(layer.get("opacity", 1))
        if layer.get("type") == "shape":
            draw.rounded_rectangle(
                (x, y, x + width, y + height),
                radius=max(0, round(float(layer.get("borderRadius", 0)) * min(sx, sy))),
                fill=_color(str(layer.get("fill", "#00b8d9")), opacity),
            )
        elif layer.get("type") == "text":
            name = str(layer.get("name", "")).casefold()
            value = (
                content.title
                if "título" in name or "title" in name
                else content.cta
                if "acción" in name or "cta" in name
                else str(layer.get("text", ""))
            )
            face = _font(
                max(8, round(float(layer.get("fontSize", 30)) * min(sx, sy))),
                float(layer.get("fontWeight", 400)) >= 650,
            )
            if layer.get("fill"):
                draw.rounded_rectangle(
                    (x, y, x + width, y + height),
                    radius=max(0, round(float(layer.get("borderRadius", 0)) * min(sx, sy))),
                    fill=_color(str(layer["fill"]), opacity),
                )
            draw.multiline_text(
                (x, y),
                value,
                font=face,
                fill=_color(str(layer.get("color", "#ffffff")), opacity),
                spacing=4,
            )
        elif layer.get("type") == "image":
            source = str(layer.get("src") or "")
            if not source.startswith("data:image/") or ";base64," not in source:
                continue
            try:
                encoded = source.split(",", 1)[1]
                if len(encoded) > 7_000_000:
                    continue
                image = Image.open(BytesIO(base64.b64decode(encoded, validate=True))).convert(
                    "RGBA"
                )
            except (OSError, ValueError, binascii.Error):
                continue
            if layer.get("fit") == "cover":
                image = ImageOps.fit(image, (width, height), Image.Resampling.LANCZOS)
            else:
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
            if opacity < 1:
                image.putalpha(
                    image.getchannel("A").point([round(value * opacity) for value in range(256)])
                )
            canvas.alpha_composite(image, (x, y))


def _metadata_critic(content: CreativeContent, variant: str, has_logo: bool) -> dict[str, Any]:
    feature_count = len(_features(content.specs))
    title_length = len(content.short_title or content.title)
    scores = {
        "hierarchy": 92 if variant in {"A", "B", "C"} else 84,
        "clarity": max(62, 96 - max(0, title_length - 55)),
        "brand": 96 if has_logo else 35,
        "product_focus": 94,
        "commercial_strength": min(94, 76 + feature_count * 5),
        "readability": max(65, 95 - max(0, title_length - 68)),
    }
    return {
        "mode": "metadata_layout",
        "vision_used": False,
        "scores": scores,
        "overall": round(sum(scores.values()) / len(scores)),
        "evidence": {
            "title_characters": title_length,
            "feature_count": feature_count,
            "real_logo_present": has_logo,
            "product_source": "transparent_cutout",
        },
    }


def render_creative(
    content: CreativeContent,
    variant: str,
    format_name: str,
    cutout_path: Path,
    background_path: Path | None = None,
    logo_path: Path | None = None,
    template_document: dict[str, Any] | None = None,
) -> RenderedCreative:
    if format_name not in FORMATS:
        raise ValueError("Formato creativo no soportado")
    policy_errors = validate_creative_policy(content)
    if policy_errors:
        raise ValueError("; ".join(policy_errors))
    cutout = _transparent_image(cutout_path)
    canvas = _background(FORMATS[format_name], variant, background_path)
    _place_product(canvas, cutout, variant, content)
    if template_document is not None:
        _render_layer_document(canvas, template_document, content)
    else:
        _draw_copy(canvas, content, variant)
    has_logo = _draw_logo(canvas, logo_path, variant)
    output = BytesIO()
    canvas.convert("RGB").save(output, "PNG", optimize=True)
    png = output.getvalue()
    qa_errors: list[str] = []
    if content.brand == "cometag" and not has_logo:
        qa_errors.append("Falta el logo real de Cometa G")
    critic = _metadata_critic(content, variant, has_logo)
    manifest = {
        "content": content.model_dump(exclude={"metadata"}),
        "layout": content.metadata.get("layout", {}),
        "variant": variant,
        "format": format_name,
        "resolution": list(canvas.size),
        "input_hash": sha256(content.model_dump_json().encode()).hexdigest(),
        "output_hash": sha256(png).hexdigest(),
        "qa": {"valid": not qa_errors, "errors": qa_errors, "approval": "pending"},
        "critic": critic,
        "renderer": "alsema.creative.pillow.v1",
    }
    return RenderedCreative(png=png, manifest=manifest, width=canvas.width, height=canvas.height)


def manifest_bytes(manifest: dict[str, Any]) -> bytes:
    return json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
