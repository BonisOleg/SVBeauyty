"""Генерація тестових зображень товарів, категорій і банерів.

Тимчасова заглушка на час, поки клієнт не передасть реальні фото.
Малюнок детермінований: той самий SKU завжди дає ту саму картинку.
"""

import random
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

PALETTE = {
    "ink": (7, 56, 53),
    "head": (21, 96, 93),
    "accent": (32, 132, 124),
    "accent_soft": (63, 168, 157),
    "line": (197, 228, 223),
    "line_soft": (226, 241, 238),
    "paper": (239, 249, 248),
    "white": (255, 255, 255),
    "gold": (165, 118, 42),
}

BACKGROUNDS = [
    ((239, 249, 248), (214, 238, 234)),
    ((246, 250, 249), (223, 240, 236)),
    ((238, 246, 245), (205, 232, 227)),
    ((250, 250, 248), (229, 242, 238)),
]

CAP_COLORS = [
    (21, 96, 93),
    (32, 132, 124),
    (7, 56, 53),
    (63, 168, 157),
    (165, 118, 42),
]

BODY_COLORS = [
    (255, 255, 255),
    (250, 253, 252),
    (240, 248, 246),
    (231, 243, 240),
]

OUTLINE = (166, 205, 199)

# Форма флакона під кожну категорію
SHAPES = {
    "pilinhy": "jar",
    "ochyshchennya": "pump",
    "tonizatsiya": "tall",
    "syrovatky": "dropper",
    "masky": "tube",
    "kremy": "jar",
    "ochi": "mini",
    "spf": "tube",
}

# Вирівнює візуальну висоту різних форм у кадрі товару
SHAPE_SCALE = {
    "jar": 1.94,
    "pump": 1.25,
    "tall": 1.25,
    "dropper": 1.45,
    "mini": 2.35,
    "tube": 1.38,
}

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

FONT_CANDIDATES_REGULAR = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _font(size: int, bold: bool = False):
    for path in FONT_CANDIDATES if bold else FONT_CANDIDATES_REGULAR:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def _gradient(size: tuple[int, int], top: tuple, bottom: tuple) -> Image.Image:
    width, height = size
    base = Image.new("RGB", (1, height))
    draw = ImageDraw.Draw(base)
    for y in range(height):
        ratio = y / max(1, height - 1)
        draw.point(
            (0, y),
            fill=tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)),
        )
    return base.resize((width, height), Image.BILINEAR)


def _soft_shadow(canvas: Image.Image, box: tuple[int, int, int, int]) -> None:
    x0, _, x1, y1 = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse([x0 - 18, y1 - 14, x1 + 18, y1 + 30], fill=(7, 56, 53, 70))
    layer = layer.filter(ImageFilter.GaussianBlur(14))
    canvas.alpha_composite(layer)


def _stage(size: tuple[int, int], top: tuple, bottom: tuple, floor_y: int) -> Image.Image:
    """Фон-градієнт з м'якою «полицею» під товаром."""
    canvas = _gradient(size, top, bottom).convert("RGBA")
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rectangle([0, floor_y, size[0], size[1]], fill=(255, 255, 255, 90))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(26)))
    return canvas


def _centered_text(draw, center_x, y, text, font, fill):
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((center_x - (box[2] - box[0]) / 2, y), text, font=font, fill=fill)
    return box[3] - box[1]


def _fit(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


BOTTLE_SIZES = {
    "jar": (300, 230),
    "pump": (210, 350),
    "tall": (176, 400),
    "dropper": (168, 268),
    "mini": (232, 180),
    "tube": (190, 380),
}


def _draw_bottle(draw, shape, cx, baseline, body_color, cap_color, scale: float = 1.0):
    """Малює силует флакона, що стоїть на лінії baseline. Повертає bbox тіла."""
    shape = shape if shape in BOTTLE_SIZES else "tall"
    base_w, base_h = BOTTLE_SIZES[shape]
    w, h = int(base_w * scale), int(base_h * scale)
    body = [cx - w // 2, baseline - h, cx + w // 2, baseline]
    top = body[1]

    def s(value: int) -> int:
        return max(2, int(value * scale))

    radius = s(30 if shape != "tube" else 60)
    draw.rounded_rectangle(body, radius=radius, fill=body_color, outline=OUTLINE, width=4)
    highlight = [body[0] + s(14), top + s(24), body[0] + s(34), body[3] - s(24)]
    if highlight[2] > highlight[0] and highlight[3] > highlight[1]:
        draw.rounded_rectangle(highlight, radius=s(10), fill=(255, 255, 255))

    if shape == "jar":
        draw.rounded_rectangle(
            [body[0] - s(12), top - s(62), body[2] + s(12), top + s(12)], radius=s(26), fill=cap_color
        )
    elif shape == "pump":
        collar = top - s(44)
        draw.rounded_rectangle([cx - s(40), collar, cx + s(40), top + s(8)], radius=s(10), fill=cap_color)
        draw.rounded_rectangle(
            [cx - s(15), collar - s(62), cx + s(15), collar + s(6)], radius=s(7), fill=cap_color
        )
        draw.rounded_rectangle(
            [cx - s(26), collar - s(88), cx + s(52), collar - s(58)], radius=s(13), fill=cap_color
        )
        draw.rounded_rectangle(
            [cx + s(30), collar - s(84), cx + s(52), collar - s(40)], radius=s(9), fill=cap_color
        )
    elif shape == "tall":
        draw.rounded_rectangle(
            [cx - s(40), top - s(74), cx + s(40), top + s(8)], radius=s(16), fill=cap_color
        )
    elif shape == "dropper":
        draw.rounded_rectangle(
            [cx - s(26), top - s(108), cx + s(26), top + s(6)], radius=s(12), fill=cap_color
        )
        draw.ellipse([cx - s(34), top - s(132), cx + s(34), top - s(84)], fill=cap_color)
    elif shape == "mini":
        draw.rounded_rectangle(
            [body[0] - s(8), top - s(48), body[2] + s(8), top + s(10)], radius=s(22), fill=cap_color
        )
    else:  # tube
        draw.rounded_rectangle(
            [body[0] + s(6), body[3] - s(34), body[2] - s(6), body[3]], radius=s(8), fill=cap_color
        )
        draw.rounded_rectangle(
            [cx - s(44), top - s(46), cx + s(44), top + s(12)], radius=s(14), fill=cap_color
        )
    return body


def _draw_label(draw, body, brand, title, volume):
    x0, y0, x1, y1 = body
    height = y1 - y0
    label = [x0 + 14, y0 + int(height * 0.34), x1 - 14, y0 + int(height * 0.78)]
    if label[3] - label[1] < 60:
        label = [x0 + 12, y0 + 18, x1 - 12, y1 - 18]

    draw.rounded_rectangle(label, radius=12, fill=PALETTE["white"], outline=OUTLINE, width=2)

    cx = (label[0] + label[2]) / 2
    inner = label[2] - label[0] - 20
    brand_font = _font(max(11, inner // 12), bold=True)
    title_font = _font(max(10, inner // 14))
    volume_font = _font(max(10, inner // 15), bold=True)

    y = label[1] + 12
    y += _centered_text(draw, cx, y, brand.upper(), brand_font, PALETTE["accent"]) + 14
    for line in _wrap(title, max(10, inner // 7)):
        y += _centered_text(draw, cx, y, line, title_font, PALETTE["ink"]) + 9
    if volume and y < label[3] - 24:
        _centered_text(draw, cx, label[3] - 24, volume, volume_font, PALETTE["head"])


def _wrap(text: str, limit: int, max_lines: int = 3) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
        else:
            lines.append(current)
            current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if not lines:
        return [_fit(text, limit)]
    lines[-1] = _fit(lines[-1], limit)
    return lines


def product_image(*, seed: str, category_slug: str, brand: str, title: str, volume: str, angle: int = 0) -> BytesIO:
    rng = random.Random(f"{seed}-{angle}")
    size = (900, 900)
    top, bottom = BACKGROUNDS[rng.randrange(len(BACKGROUNDS))]
    canvas = _stage(size, top, bottom, floor_y=790)

    shape = SHAPES.get(category_slug, "tall")
    body_color = BODY_COLORS[rng.randrange(len(BODY_COLORS))]
    cap_color = CAP_COLORS[rng.randrange(len(CAP_COLORS))]

    draw = ImageDraw.Draw(canvas)
    cx, baseline = size[0] // 2, 762
    scale = SHAPE_SCALE.get(shape, 1.0) * (1.0 if not angle else round(rng.uniform(0.86, 0.96), 2))
    if angle:
        cx += rng.randint(-50, 50)

    body = _draw_bottle(draw, shape, cx, baseline, body_color, cap_color, scale)
    _soft_shadow(canvas, body)
    draw = ImageDraw.Draw(canvas)
    _draw_bottle(draw, shape, cx, baseline, body_color, cap_color, scale)
    _draw_label(draw, body, brand, title, volume)

    buffer = BytesIO()
    canvas.convert("RGB").save(buffer, format="JPEG", quality=88, optimize=True)
    buffer.seek(0)
    return buffer


def category_image(*, seed: str, slug: str) -> BytesIO:
    """Декоративна композиція без тексту — назву виводить шаблон."""
    rng = random.Random(seed)
    size = (800, 800)
    top, bottom = BACKGROUNDS[rng.randrange(len(BACKGROUNDS))]
    canvas = _stage(size, top, bottom, floor_y=572)

    draw = ImageDraw.Draw(canvas)
    shape = SHAPES.get(slug, "tall")
    baseline = 530
    for index, (offset, scale) in enumerate(((-190, 0.5), (0, 0.7), (190, 0.5))):
        _draw_bottle(
            draw,
            shape if index == 1 else ("dropper" if index == 0 else "jar"),
            size[0] // 2 + offset,
            baseline,
            BODY_COLORS[(rng.randrange(4) + index) % len(BODY_COLORS)],
            CAP_COLORS[(rng.randrange(4) + index) % len(CAP_COLORS)],
            scale,
        )

    buffer = BytesIO()
    canvas.convert("RGB").save(buffer, format="JPEG", quality=88, optimize=True)
    buffer.seek(0)
    return buffer


def banner_image(*, size: tuple[int, int], layout: str = "desktop") -> BytesIO:
    """Декоративний фон банера. Заголовок накладає шаблон поверх зображення."""
    width, height = size
    canvas = _stage(size, PALETTE["paper"], (206, 233, 229), floor_y=int(height * 0.74))
    draw = ImageDraw.Draw(canvas)

    columns = (0.62, 0.75, 0.88) if layout == "desktop" else (0.24, 0.5, 0.76)
    baseline = int(height * (0.78 if layout == "desktop" else 0.6))
    for index, offset in enumerate(columns):
        _draw_bottle(
            draw,
            ("dropper", "tall", "jar")[index],
            int(width * offset),
            baseline,
            BODY_COLORS[index],
            CAP_COLORS[index],
            (0.42, 0.6, 0.46)[index] * (height / 620),
        )

    buffer = BytesIO()
    canvas.convert("RGB").save(buffer, format="JPEG", quality=86, optimize=True)
    buffer.seek(0)
    return buffer
