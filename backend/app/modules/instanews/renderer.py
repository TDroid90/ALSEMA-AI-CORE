from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ASSETS = Path(__file__).with_name("assets")


@dataclass(frozen=True)
class FittedText:
    lines: list[str]
    font_size: int
    line_height: int
    truncated: bool


def _font(size: int, weight: str) -> ImageFont.FreeTypeFont:
    name = "Montserrat-ExtraBold.otf" if weight == "extra_bold" else "Montserrat-Medium.otf"
    return ImageFont.truetype(str(ASSETS / name), size=size)


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _wrap(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = _clean(value).split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _ellipsize(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    suffix = "…"
    value = value.rstrip(" .,")
    while value and draw.textlength(value + suffix, font=font) > max_width:
        value = value[:-1].rstrip()
    return (value + suffix) if value else suffix


def fit_text(
    value: str,
    max_width: int,
    max_lines: int,
    maximum: int,
    minimum: int,
    ratio: float,
    weight: str,
) -> FittedText:
    draw = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    for size in range(maximum, minimum - 1, -2):
        font = _font(size, weight)
        lines = _wrap(draw, value, font, max_width)
        if len(lines) <= max_lines:
            return FittedText(lines, size, max(1, round(size * ratio)), False)
    font = _font(minimum, weight)
    lines = _wrap(draw, value, font, max_width)
    truncated = len(lines) > max_lines
    lines = lines[:max_lines]
    if truncated and lines:
        lines[-1] = _ellipsize(draw, lines[-1], font, max_width)
    return FittedText(lines, minimum, max(1, round(minimum * ratio)), truncated)


def _cover(image_bytes: bytes, size: tuple[int, int]) -> Image.Image:
    with Image.open(BytesIO(image_bytes)) as source:
        return ImageOps.fit(ImageOps.exif_transpose(source).convert("RGB"), size, Image.Resampling.LANCZOS)


def _overlay(size: tuple[int, int]) -> Image.Image:
    width, height = size
    gradient = Image.new("L", (1, height))
    pixels = gradient.load()
    stops = [(0.0, 0), (0.38, 82), (0.65, 184), (1.0, 224)]
    for y in range(height):
        position = y / max(1, height - 1)
        for index in range(1, len(stops)):
            if position <= stops[index][0]:
                left, right = stops[index - 1], stops[index]
                fraction = (position - left[0]) / (right[0] - left[0])
                pixels[0, y] = round(left[1] + (right[1] - left[1]) * fraction)
                break
    alpha = gradient.resize((width, height))
    layer = Image.new("RGBA", size, (0, 0, 0, 255))
    layer.putalpha(alpha)
    return layer


def _draw_lines(canvas: Image.Image, lines: list[str], position: tuple[int, int], font: ImageFont.FreeTypeFont, line_height: int) -> None:
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    x, y = position
    for index, line in enumerate(lines):
        shadow_draw.text((x, y + index * line_height + 3), line, font=font, fill=(0, 0, 0, 215))
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    canvas.alpha_composite(shadow)
    draw = ImageDraw.Draw(canvas)
    for index, line in enumerate(lines):
        draw.text((x, y + index * line_height), line, font=font, fill="white")


def render_social_asset(image_bytes: bytes, title: str, summary: str, category: str, template: dict[str, Any]) -> tuple[bytes, dict[str, int | bool]]:
    width, height = int(template["width"]), int(template["height"])
    safe, content, logo_config = template["safe_area"], template["content"], template["logo"]
    canvas = _cover(image_bytes, (width, height)).convert("RGBA")
    canvas.alpha_composite(_overlay((width, height)))
    content_width = width - int(safe["left"]) - int(safe["right"])
    title_fit = fit_text(
        title,
        content_width,
        int(content["title_lines"]),
        int(content["title_max"]),
        int(content["title_min"]),
        float(content["title_line_height"]),
        "extra_bold",
    )
    summary_fit = fit_text(
        summary,
        content_width,
        int(content["summary_lines"]),
        int(content["summary_max"]),
        int(content["summary_min"]),
        float(content["summary_line_height"]),
        "medium",
    )
    summary_height = len(summary_fit.lines) * summary_fit.line_height
    title_height = len(title_fit.lines) * title_fit.line_height
    summary_top = height - int(content["margin_bottom"]) - summary_height
    title_top = summary_top - int(content["summary_margin_top"]) - title_height

    draw = ImageDraw.Draw(canvas)
    category_font = _font(int(content["category_font_size"]), "medium")
    category_value = _clean(category) or "Actualidad"
    text_box = draw.textbbox((0, 0), category_value, font=category_font)
    chip_width = min(content_width, text_box[2] - text_box[0] + int(content["category_padding_x"]) * 2)
    chip_height = int(content["category_font_size"]) + int(content["category_padding_y"]) * 2
    chip_top = title_top - int(content["title_margin_top"]) - chip_height
    if chip_top < int(safe["top"]):
        raise ValueError("El texto excede el área segura de la plantilla")
    x = int(safe["left"])
    draw.rounded_rectangle((x, chip_top, x + chip_width, chip_top + chip_height), radius=int(content["category_radius"]), fill="#ffc107")
    draw.text((x + chip_width / 2, chip_top + chip_height / 2), category_value, font=category_font, fill="#06111f", anchor="mm")
    _draw_lines(canvas, title_fit.lines, (x, title_top), _font(title_fit.font_size, "extra_bold"), title_fit.line_height)
    _draw_lines(canvas, summary_fit.lines, (x, summary_top), _font(summary_fit.font_size, "medium"), summary_fit.line_height)

    badge_size = int(logo_config["badge_size"])
    badge_x = width - int(logo_config["margin_right"]) - badge_size
    badge_y = int(logo_config["margin_top"])
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((badge_x, badge_y, badge_x + badge_size, badge_y + badge_size), fill=(13, 27, 42, 235), outline=(255, 255, 255, 165), width=2)
    with Image.open(ASSETS / "instanews-isotype.png") as logo:
        mark = logo.convert("RGBA")
        mark.thumbnail((int(logo_config["logo_max_width"]), int(logo_config["logo_max_width"])), Image.Resampling.LANCZOS)
        canvas.alpha_composite(mark, (badge_x + (badge_size - mark.width) // 2, badge_y + (badge_size - mark.height) // 2))

    output = BytesIO()
    canvas.convert("RGB").save(output, "PNG", optimize=True, compress_level=9)
    return output.getvalue(), {
        "title_lines": len(title_fit.lines),
        "summary_lines": len(summary_fit.lines),
        "title_font_size": title_fit.font_size,
        "summary_font_size": summary_fit.font_size,
        "title_truncated": title_fit.truncated,
        "summary_truncated": summary_fit.truncated,
    }
