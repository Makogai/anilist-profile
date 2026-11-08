"""Shared palette, fonts and drawing helpers for the Makogai AniList profile build.

Every static asset is drawn at 2x (1440 px wide) and shown at img720 on AniList.
Colours and type follow design/PLAN.md.
"""
from functools import lru_cache
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "art"
COVERS = ROOT / "build" / "covers"
OUT = ROOT / "profile"
OUT.mkdir(exist_ok=True)

W = 1440

# Palette (design/PLAN.md section 2)
VOID = (9, 11, 24)
INDIGO = (21, 26, 61)
BLUE = (50, 184, 242)
ICE = (142, 235, 255)
VIOLET = (130, 87, 255)
MAGENTA = (240, 90, 166)
LACE = (245, 244, 255)
SILVER = (170, 182, 213)
SATIN = (17, 19, 29)
LILAC = (198, 167, 255)
CORAL = (255, 91, 121)
GOLD = (255, 205, 96)
MINT = (46, 230, 200)

# Windows fonts first; build/fonts holds the OFL Noto JP fonts the GitHub Action downloads, because
# the Windows runner has Bahnschrift and Segoe but not Noto JP (and only the older icon font).
FONT_DIRS = [Path("C:/Windows/Fonts"), ROOT / "build" / "fonts"]
FONT_FILES = {  # first file found wins
    "bahn": ["bahnschrift.ttf"],
    "segoe": ["segoeui.ttf"],
    "segoeb": ["segoeuib.ttf"],
    "serifjp": ["NotoSerifJP-VF.ttf", "NotoSerifJP[wght].ttf"],
    "sansjp": ["NotoSansJP-VF.ttf", "NotoSansJP[wght].ttf"],
    "icons": ["SegoeIcons.ttf", "segmdl2.ttf"],
}


@lru_cache(maxsize=None)
def font_path(name: str) -> Path:
    for fname in FONT_FILES[name]:
        for d in FONT_DIRS:
            if (d / fname).exists():
                return d / fname
    raise FileNotFoundError(f"no font for {name!r}: tried {FONT_FILES[name]} in {[str(d) for d in FONT_DIRS]}")


@lru_cache(maxsize=None)
def font(name: str, size: int, style: str | None = None) -> ImageFont.FreeTypeFont:
    """name: 'bahn', 'segoe', 'segoeb', 'serifjp', 'sansjp', 'icons'. style: variation name."""
    f = ImageFont.truetype(str(font_path(name)), size)
    if style:
        f.set_variation_by_name(style)
    return f


STATS = ROOT / "data" / "stats.json"


def load_stats() -> dict:
    """AniList numbers written by build/fetch_stats.py (refreshed daily by the GitHub Action)."""
    import json
    return json.loads(STATS.read_text(encoding="utf-8"))


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(w, h, stops, angle="h"):
    """RGBA gradient. stops: [(pos 0..1, (r,g,b) or (r,g,b,a)), ...]; angle 'h', 'v' or 'd'."""
    if angle == "h":
        t = np.tile(np.linspace(0, 1, w, dtype=np.float32), (h, 1))
    elif angle == "v":
        t = np.tile(np.linspace(0, 1, h, dtype=np.float32)[:, None], (1, w))
    else:
        x = np.linspace(0, 1, w, dtype=np.float32)[None, :]
        y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        t = np.clip(x * 0.75 + y * 0.25, 0, 1)
    pos = [s[0] for s in stops]
    out = np.zeros((h, w, 4), np.float32)
    for ch in range(4):
        vals = [(s[1][ch] if ch < len(s[1]) else 255) for s in stops]
        out[..., ch] = np.interp(t, pos, vals)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


BLUE_VIOLET = [(0, BLUE), (1, VIOLET)]
ICE_VIOLET = [(0, ICE), (0.45, BLUE), (1, VIOLET)]
# extra title gradients so sections don't all share one colour
ICE_PINK = [(0, ICE), (0.5, BLUE), (1, MAGENTA)]
MINT_BLUE = [(0, MINT), (1, BLUE)]
MINT_PINK = [(0, MINT), (0.5, VIOLET), (1, MAGENTA)]
PINK_VIOLET = [(0, MAGENTA), (1, VIOLET)]
GOLD_CORAL = [(0, GOLD), (1, CORAL)]
RAINBOW = [(0, CORAL), (0.25, GOLD), (0.5, MINT), (0.75, BLUE), (1, VIOLET)]


def blur_glow(layer: Image.Image, radius: float, strength: float = 1.0) -> Image.Image:
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        a = np.asarray(g, np.float32)
        a[..., 3] = np.clip(a[..., 3] * strength, 0, 255)
        g = Image.fromarray(a.astype(np.uint8), "RGBA")
    return g


def text_mask(size, xy, text, fnt, anchor="la", tracking=0, stroke=0):
    """Return an L mask with the text drawn (supports letter tracking)."""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    if not tracking:
        d.text(xy, text, font=fnt, fill=255, anchor=anchor, stroke_width=stroke, stroke_fill=255)
        return m
    # manual tracking: measure total width first, then honour horizontal anchor
    widths = [d.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    va = "l" + anchor[1]
    for ch, cw in zip(text, widths):
        d.text((x, y), ch, font=fnt, fill=255, anchor=va, stroke_width=stroke, stroke_fill=255)
        x += cw + tracking
    return m


def draw_text(base: Image.Image, xy, text, fnt, fill=LACE, anchor="la", tracking=0,
              glow=None, glow_radius=10, glow_strength=1.0, gradient_stops=None,
              shadow=True):
    """Draw text onto an RGBA base with optional gradient fill, glow and soft drop shadow."""
    m = text_mask(base.size, xy, text, fnt, anchor, tracking)
    if shadow:
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        sh.putalpha(m.filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.65)))
        base.alpha_composite(sh, (0, 4))
    if glow:
        gl = Image.new("RGBA", base.size, rgba(glow))
        gl.putalpha(m)
        base.alpha_composite(blur_glow(gl, glow_radius, glow_strength))
    bbox = m.getbbox()
    if not bbox:
        return bbox
    if gradient_stops:
        x0, y0, x1, y1 = bbox
        g = gradient(x1 - x0, y1 - y0, gradient_stops, "h")
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(g, (x0, y0))
    else:
        layer = Image.new("RGBA", base.size, rgba(fill) if len(fill) == 3 else fill)
    a = np.minimum(np.asarray(layer.getchannel("A"), np.uint16), np.asarray(m, np.uint16))
    layer.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    base.alpha_composite(layer)
    return bbox


def wrap(text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if fnt.getlength(t) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def draw_rich(base, x, y, segments, size, max_w, line_h):
    """Body copy with inline emphasis. segments: [(text, bold:bool, colour)]. Returns end y."""
    reg, bold, jp = font("segoe", size), font("segoeb", size), font("sansjp", size, "Bold")
    d = ImageDraw.Draw(base)
    cx, cy = x, y
    for text, is_bold, col in segments:
        for word in text.split(" "):
            if word == "":
                continue
            # Segoe UI has no CJK glyphs, so words with kanji/kana fall back to Noto Sans JP
            f = jp if any(ord(c) >= 0x3000 for c in word) else (bold if is_bold else reg)
            if word == "\n":
                cx, cy = x, cy + line_h
                continue
            piece = word + " "
            wlen = f.getlength(piece)
            if cx + f.getlength(word) > x + max_w:
                cx, cy = x, cy + line_h
            d.text((cx + 2, cy + 3), piece, font=f, fill=(0, 0, 0, 150))
            d.text((cx, cy), piece, font=f, fill=rgba(col))
            cx += wlen
    return cy + line_h


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    return m


def cover(img: Image.Image, size, focus=(0.5, 0.5)) -> Image.Image:
    """Scale and crop img to fill size, keeping the focus point (fractions) in view."""
    w, h = size
    s = max(w / img.width, h / img.height)
    r = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x = int((r.width - w) * focus[0])
    y = int((r.height - h) * focus[1])
    return r.crop((x, y, x + w, y + h))


def darken(img: Image.Image, f: float) -> Image.Image:
    a = np.asarray(img.convert("RGBA"), np.float32)
    a[..., :3] *= f
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def screen(base: Image.Image, over: Image.Image, opacity=1.0, pos=(0, 0)) -> Image.Image:
    """Screen-blend an RGB(A) image (black = transparent) onto base in place."""
    region = (pos[0], pos[1], pos[0] + over.width, pos[1] + over.height)
    b = np.asarray(base.crop(region).convert("RGBA"), np.float32) / 255
    o = np.asarray(over.convert("RGBA"), np.float32) / 255
    oa = o[..., 3:4] * opacity
    res = 1 - (1 - b[..., :3]) * (1 - o[..., :3] * oa)
    b[..., :3] = res
    base.paste(Image.fromarray((b * 255).astype(np.uint8), "RGBA"), region[:2])
    return base


def black_to_alpha(rgb: np.ndarray, floor=18, gain=1.15) -> Image.Image:
    """Turn art on a black background into RGBA. The noise floor is cut to fully transparent,
    because the generated 'black' is grainy and that grain would bloat the WebP."""
    lum = rgb.max(axis=2)
    alpha = np.clip((lum - floor) * (255 / (255 - floor)) * gain, 0, 255)
    un = np.where(alpha[..., None] > 0, rgb * 255 / np.maximum(lum[..., None], 1), 0)
    return Image.fromarray(np.dstack([np.clip(un, 0, 255), alpha]).astype(np.uint8), "RGBA")


def gradient_map(rgb: np.ndarray, ramp, floor=14):
    """Recolour neutral art on black: luminance -> colour ramp [(pos, (r,g,b)), ...]; black -> transparent."""
    lum = rgb.max(axis=2)
    t = np.clip(lum / 255, 0, 1)
    out = np.zeros(rgb.shape[:2] + (4,), np.float32)
    pos = [p for p, _ in ramp]
    for ch in range(3):
        out[..., ch] = np.interp(t, pos, [c[ch] for _, c in ramp])
    out[..., 3] = np.clip((lum - floor) * 10, 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def vignette(img: Image.Image, strength=0.55) -> Image.Image:
    w, h = img.size
    y, x = np.ogrid[-1:1:h * 1j, -1:1:w * 1j]
    v = 1 - strength * np.clip((x ** 2 * 0.6 + y ** 2 * 0.9), 0, 1)
    a = np.asarray(img.convert("RGBA"), np.float32)
    a[..., :3] *= v[..., None]
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def sparkle(d: ImageDraw.ImageDraw, x, y, r, col, alpha=255):
    """Four-point star."""
    c = rgba(col, alpha)
    t = max(1, r // 6)
    d.polygon([(x, y - r), (x + t, y - t), (x + r, y), (x + t, y + t),
               (x, y + r), (x - t, y + t), (x - r, y), (x - t, y - t)], fill=c)


def particles(size, n, seed, colours=(ICE, BLUE, LACE, LILAC), rmax=10, star_ratio=0.3,
              alpha=(90, 230)) -> Image.Image:
    rng = random.Random(seed)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = rng.uniform(0, size[0]), rng.uniform(0, size[1])
        col = rng.choice(colours)
        a = rng.randint(*alpha)
        if rng.random() < star_ratio:
            sparkle(d, x, y, rng.randint(5, rmax * 2), col, a)
        else:
            r = rng.uniform(1, rmax / 3)
            d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(col, a))
    glow = blur_glow(layer, 6, 1.4)
    glow.alpha_composite(layer)
    return glow


def card_frame(size, radius=36, width=4, stops=ICE_VIOLET, glow_col=BLUE, inset=14):
    """Gradient keyline frame with outer glow and an inner thin line, as a transparent overlay."""
    w, h = size
    ring = Image.new("L", size, 0)
    d = ImageDraw.Draw(ring)
    d.rounded_rectangle((inset, inset, w - 1 - inset, h - 1 - inset), radius, outline=255, width=width)
    g = gradient(w, h, stops, "d")
    g.putalpha(ring)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    gl = Image.new("RGBA", size, rgba(glow_col))
    gl.putalpha(ring)
    out.alpha_composite(blur_glow(gl, 12, 1.6))
    out.alpha_composite(g)
    inner = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(inner).rounded_rectangle(
        (inset + 12, inset + 12, w - 1 - inset - 12, h - 1 - inset - 12), max(4, radius - 10),
        outline=rgba(LACE, 40), width=2)
    out.alpha_composite(inner)
    return out


def ribbon_x(d: ImageDraw.ImageDraw, cx, cy, r, col=MAGENTA, width=6):
    d.line((cx - r, cy - r, cx + r, cy + r), fill=rgba(col), width=width)
    d.line((cx - r, cy + r, cx + r, cy - r), fill=rgba(col), width=width)


def diamond(d: ImageDraw.ImageDraw, cx, cy, r, fill=None, outline=None, width=2):
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    d.polygon(pts, fill=fill, outline=outline, width=width)


def panel_base(h, bg="night", focus=(0.5, 0.5), dim=0.85, radius=40):
    """Dark card background: 'night' (navy sky) or 'aurora' (teal/violet/pink ribbons)."""
    if isinstance(bg, str):
        bg = Image.open(ART / f"bg-{bg}.png").convert("RGBA")
    base = darken(cover(bg, (W, h), focus), dim)
    tint = gradient(W, h, [(0, rgba(VOID, 120)), (0.5, rgba(INDIGO, 40)), (1, rgba(VOID, 140))], "v")
    base.alpha_composite(tint)
    base = vignette(base, 0.45)
    return base


def chamfer_poly(w, h, c, inset=0):
    i = inset
    return [(i + c, i), (w - 1 - i - c, i), (w - 1 - i, i + c), (w - 1 - i, h - 1 - i - c),
            (w - 1 - i - c, h - 1 - i), (i + c, h - 1 - i), (i, h - 1 - i - c), (i, i + c)]


def chamfer_frame(size, c, stops, glow_col, inset=6, width=4):
    ring = Image.new("L", size, 0)
    ImageDraw.Draw(ring).polygon(chamfer_poly(*size, c, inset), outline=255, width=width)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    gl = Image.new("RGBA", size, rgba(glow_col))
    gl.putalpha(ring)
    out.alpha_composite(blur_glow(gl, 12, 1.6))
    g = gradient(*size, stops, "d")
    g.putalpha(ring)
    out.alpha_composite(g)
    return out


def card_finisher(size, radius=40, stops=ICE_VIOLET, glow_col=BLUE):
    """finish_card for many animation frames of one size: frame overlay and mask are built once."""
    overlay = card_frame(size, radius=radius - 8, stops=stops, inset=6, glow_col=glow_col)
    mask = np.asarray(rounded_mask(size, radius))

    def apply(img: Image.Image) -> Image.Image:
        img.alpha_composite(overlay)
        img.putalpha(Image.fromarray(np.minimum(np.asarray(img.getchannel("A")), mask), "L"))
        return img
    return apply


def finish_card(img: Image.Image, radius=40, frame=True, stops=ICE_VIOLET, shape="round",
                glow_col=BLUE) -> Image.Image:
    """Clip to a rounded (or chamfered, 'tech' style) card and add the glowing frame."""
    if shape == "chamfer":
        if frame:
            img.alpha_composite(chamfer_frame(img.size, radius + 10, stops, glow_col))
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).polygon(chamfer_poly(*img.size, radius + 4), fill=255)
        a = np.minimum(np.asarray(img.getchannel("A")), np.asarray(mask))
        img.putalpha(Image.fromarray(a, "L"))
        return img
    if frame:
        img.alpha_composite(card_frame(img.size, radius=radius - 8, stops=stops, inset=6, glow_col=glow_col))
    mask = rounded_mask(img.size, radius)
    a = np.minimum(np.asarray(img.getchannel("A")), np.asarray(mask))
    img.putalpha(Image.fromarray(a, "L"))
    return img


def save(img: Image.Image, name: str, quality=88):
    """Save as lossy WebP with alpha (much lighter than PNG for painterly panels)."""
    path = OUT / name
    if name.endswith(".webp"):
        img.save(path, "WEBP", quality=quality, method=6, alpha_quality=90)
    elif name.endswith(".png"):
        img.save(path, "PNG", optimize=True)
    else:
        img.convert("RGB").save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    print(f"{name}: {img.size[0]}x{img.size[1]}, {path.stat().st_size / 1024:.0f} KB")
    return path


def section_title(img, y, label, title, jp, x=None, align="m", rule=True, jp_on_label=False,
                  stops=ICE_VIOLET, glow=BLUE, label_col=ICE):
    """Small tracked label, big gradient title with glow, Japanese accent beside it."""
    cx = W // 2 if x is None else x
    anchor = {"m": "m", "l": "l", "r": "r"}[align]
    lb = draw_text(img, (cx, y), label, font("bahn", 32, "SemiBold"), fill=label_col, anchor=anchor + "s",
                   tracking=8, shadow=False)
    tx = cx
    jp_w = 24 + font("serifjp", 44, "Bold").getlength(jp) if jp and not jp_on_label else 0
    if align == "m":
        tx = cx - jp_w / 2  # centre title + Japanese accent as one group
    elif align == "r":
        tx = cx - jp_w
    bbox = draw_text(img, (tx, y + 92), title, font("bahn", 86, "Bold"), anchor=anchor + "s",
                     tracking=6, gradient_stops=stops, glow=glow, glow_radius=16, glow_strength=1.1)
    if jp and jp_on_label:
        lx = lb[2] + 28 if align != "r" else lb[0] - 28
        draw_text(img, (lx, y + 2), jp, font("serifjp", 36, "Bold"), fill=LILAC,
                  anchor="ls" if align != "r" else "rs", glow=VIOLET, glow_radius=8)
    elif jp:
        draw_text(img, (bbox[2] + 24, y + 88), jp, font("serifjp", 44, "Bold"), fill=LILAC, anchor="ls",
                  glow=VIOLET, glow_radius=10)
    ry = y + 124
    if not rule:
        return ry
    d = ImageDraw.Draw(img)
    if align == "m":
        x0, x1 = cx - 260, cx + 260
        line = gradient(x1 - x0, 3, [(0, rgba(stops[0][1], 0)), (0.5, rgba(stops[0][1], 255)),
                                     (1, rgba(stops[-1][1], 0))])
        mx = cx
    elif align == "l":
        x0, x1 = cx, cx + 520
        line = gradient(x1 - x0, 3, [(0, rgba(stops[0][1], 255)), (1, rgba(stops[-1][1], 0))])
        mx = x0 + 40
    else:
        x0, x1 = cx - 520, cx
        line = gradient(x1 - x0, 3, [(0, rgba(stops[0][1], 0)), (1, rgba(stops[-1][1], 255))])
        mx = x1 - 40
    img.alpha_composite(line, (int(x0), ry))
    diamond(d, mx, ry + 1, 9, fill=rgba(VOID), outline=rgba(stops[0][1]), width=3)
    return ry + 20


def glass(img, box, tint=BLUE, radius=28, alpha=150, shape="round"):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = gradient(w, h, [(0, rgba(INDIGO, alpha)), (1, rgba(VOID, alpha + 40))], "v")
    shine = gradient(w, h, [(0, rgba(tint, 70)), (0.35, rgba(tint, 0))], "d")
    layer.alpha_composite(shine)
    if shape == "chamfer":
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).polygon(chamfer_poly(w, h, radius), fill=255)
    else:
        m = rounded_mask((w, h), radius)
    layer.putalpha(Image.fromarray(np.minimum(np.asarray(layer.getchannel("A")), np.asarray(m)), "L"))
    img.alpha_composite(layer, (x0, y0))
    border = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    if shape == "chamfer":
        bd.polygon(chamfer_poly(w, h, radius), outline=rgba(tint, 210), width=3)
    else:
        bd.rounded_rectangle((0, 0, w - 1, h - 1), radius, outline=rgba(tint, 200), width=3)
    img.alpha_composite(blur_glow(border, 8, 1.2), (x0, y0))
    img.alpha_composite(border, (x0, y0))


def rotated(img: Image.Image, angle: float) -> Image.Image:
    return img.rotate(angle, resample=Image.BICUBIC, expand=True)
