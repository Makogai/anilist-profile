"""Waifu collection (a side piece, not on the main About page): ten animated rank cards in the spirit of
gacha card games (R, SR, SSR, UR, LR), each rank with its own border, aura and effects, plus a header with
the rank legend. Output goes to profile/waifus/; make_about.py writes waifus.md to paste wherever wanted.
The showcase site (index.html, GitHub Pages) reads profile/waifus/waifus.json and the full-size cards in
profile/waifus/hd/, so adding a waifu = Codex art + a WAIFUS entry + `python build/waifus.py <key>`.

The cards form a pyramid, one row per rank group, higher ranks bigger: LR (1) / UR (2) / SSR (3) /
SR + R (4). Each card is its own animated WebP, rendered at twice the width AniList shows it at.

Run: python build/waifus.py [key ...]   (no keys: header + all cards; the manifest is rewritten every run)
"""
import json
import math
import sys
import zlib

import numpy as np
from PIL import Image, ImageDraw

from animated import save_anim, shine_band
from common import (ART, BLUE, CORAL, GOLD, ICE, LACE, LILAC, MAGENTA, MINT, OUT, SATIN, VIOLET, VOID, W,
                    blur_glow, cover, draw_text, finish_card, font, gradient, mix, panel_base, particles, rgba,
                    rounded_mask, save, section_title, sparkle)

SUB = "waifus/"  # output subfolder of profile/
(OUT / SUB / "hd").mkdir(parents=True, exist_ok=True)

CW, CH = 460, 690          # card
M = 40                     # margin around the card for aura, rays and the LR crown
SW, SH = CW + 2 * M, CH + 2 * M
BW = 16                    # border width
RAD = 34                   # outer corner radius

SAPPHIRE = [(0, (170, 215, 255)), (0.5, (90, 150, 240)), (1, (45, 90, 190))]
AMETHYST = [(0, (225, 200, 255)), (0.5, LILAC), (1, (110, 60, 220))]
GOLD_METAL = [(0, (255, 244, 200)), (0.35, GOLD), (0.7, (210, 140, 40)), (1, (255, 225, 150))]
PRISM = [(0, CORAL), (0.25, GOLD), (0.5, MINT), (0.75, BLUE), (1, VIOLET)]

# level = stars; out = rendered width (2x the css width the row shows it at)
RANKS = {
    "R": dict(level=1, out=240, stops=SAPPHIRE, glow=(90, 160, 255), name="RARE", frames=20),
    "SR": dict(level=2, out=240, stops=AMETHYST, glow=VIOLET, name="SUPER RARE", frames=20),
    "SSR": dict(level=3, out=320, stops=GOLD_METAL, glow=GOLD, name="SUPER SUPER RARE", frames=24),
    "UR": dict(level=4, out=400, stops=PRISM, glow=MAGENTA, name="ULTRA RARE", frames=24),
    "LR": dict(level=5, out=440, stops=[(0, GOLD), (0.5, MAGENTA), (1, VIOLET)], glow=MAGENTA, name="LEGENDARY",
               frames=26),
}

WAIFUS = [  # key, name, Japanese name, series, rank
    ("rem", "REM", "レム", "RE:ZERO", "LR"),
    ("zerotwo", "ZERO TWO", "ゼロツー", "DARLING IN THE FRANXX", "UR"),
    ("iroha", "IROHA", "色葉", "3D KANOJO: REAL GIRL", "UR"),
    ("mai", "MAI", "麻衣", "BUNNY GIRL SENPAI", "SSR"),
    ("emilia", "EMILIA", "エミリア", "RE:ZERO", "SSR"),
    ("raphtalia", "RAPHTALIA", "ラフタリア", "SHIELD HERO", "SSR"),
    ("hori", "HORI", "京子", "HORIMIYA", "SR"),
    ("yukino", "YUKINO", "雪乃", "OREGAIRU", "SR"),
    ("horikita", "HORIKITA", "鈴音", "CLASSROOM OF THE ELITE", "R"),
    ("shiro", "SHIRO", "白", "NO GAME NO LIFE", "R"),
]
ANILIST = {  # AniList character ids, for links on the showcase site
    "rem": 88575, "zerotwo": 124381, "iroha": 83237, "mai": 127222, "emilia": 88572, "raphtalia": 88889,
    "hori": 66171, "yukino": 67067, "horikita": 123213, "shiro": 82525,
}
COLUMN = 514  # AniList About column width in css px (measured)


def pyramid():
    """Rows for waifus.md: highest rank first; cards shown at the same width share rows, as many per row as
    fit the AniList column (LR/UR 2, SSR 3, SR/R 4)."""
    ranked = sorted(WAIFUS, key=lambda w: -RANKS[w[4]]["level"])  # stable: list order within a rank
    rows, group, width = [], [], None

    def flush():
        per_row = (COLUMN + 4) // (width + 4)
        rows.extend(group[i:i + per_row] for i in range(0, len(group), per_row))

    for w in ranked:
        css = RANKS[w[4]]["out"] // 2
        if group and css != width:
            flush()
            group = []
        width = css
        group.append(w[0])
    if group:
        flush()
    return rows


PYRAMID = pyramid()

# ---------------------------------------------------------------- geometry shared by every card

YY, XX = np.mgrid[0:SH, 0:SW].astype(np.float32)
CX, CY = SW / 2, SH / 2


def _rrect_sdf(hw, hh, r):
    qx = np.abs(XX - CX) - (hw - r)
    qy = np.abs(YY - CY) - (hh - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


SDF = _rrect_sdf(CW / 2, CH / 2, RAD)                       # < 0 inside the card
CARD = np.clip(0.5 - SDF, 0, 1)                              # antialiased masks
ART_M = np.clip(-(SDF + BW) + 0.5, 0, 1)
BORDER = CARD * (1 - ART_M)
OUTSIDE = np.clip(SDF, 0, None)
U = np.clip(-SDF / BW, 0, 1)                                 # 0 = outer edge of the border, 1 = inner edge
BEVEL = 0.55 + 0.5 * (1 - np.abs(2 * U - 1)) ** 0.6           # bright ridge along the middle of the border
ANG = (np.arctan2((YY - CY) / CH, (XX - CX) / CW) / (2 * math.pi)) % 1   # 0..1 around the card
ANG_TRUE = np.arctan2(YY - CY, XX - CX)                      # even angles, for rays
DIAG = np.clip((XX - M) / CW * 0.6 + (YY - M) / CH * 0.4, 0, 1)


def ramp(t, stops):
    t = np.asarray(t, np.float32)
    pos = [p for p, _ in stops]
    return np.stack([np.interp(t, pos, [c[i] for _, c in stops]) for i in range(3)], axis=-1)


def hsv(h, s, v):
    """Vectorised HSV (0..1) -> RGB (0..255)."""
    h = (h % 1) * 6
    i = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    s_ = np.broadcast_to
    v, p, q, t = (s_(np.asarray(x, np.float32), h.shape) for x in (v, p, q, t))
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1) * 255


def over(base, rgb, a):
    """Composite a colour layer (rgb HxWx3 or colour, alpha HxW in 0..1) over base (HxWx4 straight alpha)."""
    a = np.clip(a, 0, 1)[..., None]
    ba = base[..., 3:4]
    out_a = a + ba * (1 - a)
    rgb = np.broadcast_to(np.asarray(rgb, np.float32), base[..., :3].shape)
    base[..., :3] = (rgb * a + base[..., :3] * ba * (1 - a)) / np.maximum(out_a, 1e-6)
    base[..., 3:4] = out_a


def over_img(base, img: Image.Image):
    a = np.asarray(img, np.float32)
    over(base, a[..., :3], a[..., 3] / 255)


def star_points(cx, cy, r, inner=0.45):
    return [(cx + (r if k % 2 == 0 else r * inner) * math.sin(math.pi * k / 5),
             cy - (r if k % 2 == 0 else r * inner) * math.cos(math.pi * k / 5)) for k in range(10)]


# ---------------------------------------------------------------- rank badge (also used in the legend)

def rank_badge(img, x, y, rank, h=48):
    """Chamfered plate with the rank letters; returns its width."""
    f = font("bahn", int(h * 0.72), "Bold")
    tw = f.getlength(rank) + 3 * (len(rank) - 1)
    w = int(tw + h * 0.9)
    c = int(h * 0.3)
    poly = [(c, 0), (w, 0), (w, h - c), (w - c, h), (0, h), (0, c)]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    dark = rank in ("LR", "UR")  # gradient letters need a dark plate to stay readable
    plate = gradient(w, h, [(0, (25, 12, 45)), (1, (60, 25, 90))] if dark else RANKS[rank]["stops"], "d")
    plate.putalpha(m)
    glow = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    glow.paste(Image.new("RGBA", (w, h), rgba(RANKS[rank]["glow"], 200)), (20, 20), m)
    img.alpha_composite(blur_glow(glow, 8, 1.4), (x - 20, y - 20))
    img.alpha_composite(plate, (x, y))
    d = ImageDraw.Draw(img)
    d.polygon([(x + px, y + py) for px, py in poly], outline=rgba(GOLD if rank == "LR" else LACE, 230), width=2)
    if rank in ("LR", "UR"):
        draw_text(img, (x + w / 2, y + h / 2 + 1), rank, f, anchor="mm", tracking=3,
                  gradient_stops=PRISM if rank == "UR" else [(0, (255, 240, 170)), (0.5, GOLD), (1, MAGENTA)],
                  glow=None, shadow=True)
    else:
        draw_text(img, (x + w / 2, y + h / 2 + 1), rank, f, fill=SATIN if rank != "SR" else LACE, anchor="mm",
                  tracking=3, shadow=False)
    return w


def stars(img, x, y, rank, size=12, gap=30):
    d = ImageDraw.Draw(img)
    level = RANKS[rank]["level"]
    for i in range(level):
        col = mix(PRISM[i % 5][1], LACE, 0.15) if rank in ("UR", "LR") else RANKS[rank]["stops"][1][1]
        d.polygon(star_points(x + i * gap, y, size), fill=rgba(col), outline=rgba(LACE, 180))


# ---------------------------------------------------------------- one card

def card_static(key, name, jp, series, rank):
    """Art, border base and all text for one card, as float layers (art+border) and an RGBA overlay."""
    r = RANKS[rank]
    base = np.zeros((SH, SW, 4), np.float32)
    art = cover(Image.open(ART / f"waifu-{key}.png").convert("RGBA"), (CW - 2 * BW + 2, CH - 2 * BW + 2), (0.5, 0.0))
    art.alpha_composite(gradient(art.width, art.height, [(0, (0, 0, 0, 0)), (0.62, (0, 0, 0, 0)),
                                                         (0.8, rgba(VOID, 205)), (1, rgba(VOID, 250))], "v"))
    canvas = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    canvas.paste(art, (M + BW - 1, M + BW - 1))
    art_rgb = np.asarray(canvas, np.float32)[..., :3]
    over(base, art_rgb, ART_M)

    if rank in ("R", "SR", "SSR"):  # static metal border
        col = ramp(DIAG, r["stops"])
        if rank == "SSR":
            col = col * (0.86 + 0.14 * np.cos(2 * math.pi * DIAG * 7))[..., None]  # brushed-gold bands
        over(base, np.clip(col * BEVEL[..., None], 0, 255), BORDER)

    top = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    # inner keyline
    d.rounded_rectangle((M + BW, M + BW, M + CW - BW - 1, M + CH - BW - 1), RAD - BW,
                        outline=rgba(LACE, 150 if rank != "LR" else 200), width=2)
    # corner ornaments
    corners = [(M + 15, M + 15), (M + CW - 15, M + 15), (M + 15, M + CH - 15), (M + CW - 15, M + CH - 15)]
    if rank == "SR":
        for cx, cy in corners:
            d.polygon([(cx, cy - 10), (cx + 10, cy), (cx, cy + 10), (cx - 10, cy)], fill=rgba(MAGENTA),
                      outline=rgba(LACE), width=2)
    if rank in ("SSR", "LR"):
        for cx, cy in corners:
            g = gradient(36, 36, GOLD_METAL, "d")
            m = Image.new("L", (36, 36), 0)
            ImageDraw.Draw(m).ellipse((0, 0, 35, 35), fill=255)
            g.putalpha(m)
            top.alpha_composite(g, (int(cx - 18), int(cy - 18)))
            d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), outline=rgba((120, 70, 10)), width=2)
            d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=rgba(MAGENTA if rank == "LR" else CORAL),
                      outline=rgba(LACE), width=2)
        for cx in (M + CW / 2 - 60, M + CW / 2 + 60):  # side gems on the bottom edge
            d.polygon([(cx, M + CH - 8 - 9), (cx + 9, M + CH - 8), (cx, M + CH - 8 + 9), (cx - 9, M + CH - 8)],
                      fill=rgba(ICE), outline=rgba(LACE), width=1)
    if rank == "LR":  # crown breaking the top border
        cx, cy = M + CW / 2, M + 4
        crown = [(cx - 58, cy + 16), (cx - 66, cy - 26), (cx - 30, cy - 4), (cx, cy - 40), (cx + 30, cy - 4),
                 (cx + 66, cy - 26), (cx + 58, cy + 16)]
        cm = Image.new("L", (SW, SH), 0)
        ImageDraw.Draw(cm).polygon(crown, fill=255)
        glow = Image.new("RGBA", (SW, SH), rgba(GOLD))
        glow.putalpha(cm)
        top.alpha_composite(blur_glow(glow, 10, 1.6))
        g = gradient(SW, SH, [(0, (255, 248, 210)), (0.06, GOLD), (0.1, (200, 130, 30))], "v")
        g.putalpha(cm)
        top.alpha_composite(g)
        d.polygon(crown, outline=rgba((120, 70, 10)), width=3)
        for px, py, col in ((cx - 66, cy - 26, ICE), (cx, cy - 40, MAGENTA), (cx + 66, cy - 26, ICE)):
            d.ellipse((px - 9, py - 9, px + 9, py + 9), fill=rgba(col), outline=rgba(LACE), width=2)
        d.ellipse((cx - 8, cy - 2, cx + 8, cy + 14), fill=rgba(MAGENTA), outline=rgba(LACE), width=2)

    # rank badge, Japanese name rail, series, name, stars, rank name
    rank_badge(top, M + BW + 14, M + BW + 16 + (12 if rank == "LR" else 0), rank)
    rail_x = M + CW - BW - 34
    rail = Image.new("RGBA", (40, 40 + 46 * len(jp)), (0, 0, 0, 0))
    rail.paste(Image.new("RGBA", rail.size, rgba(SATIN, 175)), (0, 0), rounded_mask(rail.size, 12))
    top.alpha_composite(rail, (rail_x - 20, M + BW + 16))
    for i, ch in enumerate(jp):
        draw_text(top, (rail_x, M + BW + 56 + i * 46), ch, font("serifjp", 34, "Bold"), fill=LACE, anchor="mm",
                  glow=r["glow"], glow_radius=6, shadow=False)
    accent = r["stops"][0][1] if rank not in ("UR", "LR") else (255, 220, 240)
    sf, size = 29, 29
    while font("bahn", size, "SemiBold").getlength(series) + 2 * len(series) > CW - 2 * BW - 40:
        size -= 1
    draw_text(top, (M + BW + 20, M + CH - 150), series, font("bahn", size, "SemiBold"), fill=accent, anchor="ls",
              tracking=2, shadow=True)
    size = 80
    while font("bahn", size, "Bold").getlength(name) + 6 * len(name) > CW - 2 * BW - 40:
        size -= 2
    name_stops = [(0, LACE), (0.45, mix(r["stops"][0][1], LACE, 0.3)), (1, r["stops"][-1][1])] \
        if rank not in ("UR", "LR") else [(0, LACE), (0.4, (255, 200, 230)), (1, MAGENTA)] if rank == "LR" \
        else [(0, LACE), (0.4, MINT), (1, VIOLET)]
    draw_text(top, (M + BW + 16, M + CH - 76), name, font("bahn", size, "Bold"), anchor="ls", tracking=6,
              gradient_stops=name_stops, glow=r["glow"], glow_radius=14)
    stars(top, M + BW + 30, M + CH - 44, rank)
    rf = 24
    while font("bahn", rf, "SemiBold").getlength(r["name"]) + 3 * len(r["name"]) > CW - 2 * BW - 150:
        rf -= 1
    draw_text(top, (M + CW - BW - 22, M + CH - 34), r["name"], font("bahn", rf, "SemiBold"),
              fill=mix(accent, LACE, 0.3), anchor="rs", tracking=3, shadow=False)
    return base, top


def card_frames(key, name, jp, series, rank):
    r = RANKS[rank]
    base, top = card_static(key, name, jp, series, rank)
    n = r["frames"]
    rng = np.random.default_rng(zlib.crc32(key.encode()))
    frames = []
    # particle sets (positions as fractions of the card)
    twinkles = [(rng.uniform(M + 40, M + CW - 40), rng.uniform(M + 60, M + CH * 0.55), rng.uniform(0, 1),
                 rng.uniform(8, 16)) for _ in range({"R": 4, "SR": 6, "SSR": 5, "UR": 8, "LR": 8}[rank])]
    glitter = [(rng.uniform(M + BW, M + CW - BW), rng.uniform(0, 1), rng.uniform(0.6, 1.4), rng.uniform(0, 1))
               for _ in range(22)]
    petals = [(rng.uniform(0, SW), rng.uniform(0, 1), rng.uniform(0, 1), rng.integers(0, 3)) for _ in range(14)]
    for i in range(n):
        t = i / n
        f = np.zeros((SH, SW, 4), np.float32)
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t)

        # aura and rays outside the card
        if rank == "UR":
            over(f, hsv(ANG + t, 0.7, 1.0), np.exp(-OUTSIDE / 16) * (OUTSIDE > 0) * 0.85)
        elif rank == "LR":
            rays = (0.5 + 0.5 * np.cos(18 * ANG_TRUE + 2 * math.pi * t)) ** 8 * np.exp(-OUTSIDE / 30) * (OUTSIDE > 0)
            over(f, ramp(ANG, [(0, GOLD), (0.5, MAGENTA), (1, GOLD)]), np.exp(-OUTSIDE / 18) * (OUTSIDE > 0)
                 * (0.6 + 0.35 * pulse) + rays * 0.6)
        else:
            sigma = {"R": 7, "SR": 9, "SSR": 13}[rank]
            strength = {"R": 0.5, "SR": 0.6, "SSR": 0.55 + 0.35 * pulse}[rank]
            over(f, r["glow"], np.exp(-OUTSIDE / sigma) * (OUTSIDE > 0) * strength)

        # card body (art + static border)
        over(f, base[..., :3], base[..., 3])

        # animated borders
        if rank == "UR":
            over(f, np.clip(hsv(ANG + t, 0.62, 1.0) * BEVEL[..., None], 0, 255), BORDER)
        elif rank == "LR":
            dark = ramp(DIAG, [(0, (40, 20, 80)), (0.5, (90, 30, 120)), (1, (40, 20, 80))])
            sheen = hsv(ANG * 2 + t, 0.5, 1.0) * 0.35
            col = np.clip((dark + sheen) * BEVEL[..., None], 0, 255)
            over(f, col, BORDER)
            for off in (0.0, 0.5):  # two comets orbiting the border
                da = ((ANG - (t + off)) % 1)  # distance behind the comet head
                head = np.exp(-(np.minimum(da, 1 - da) / 0.012) ** 2)
                tail = np.exp(-da / 0.08) * (da < 0.5)
                over(f, ramp(np.clip(da * 6, 0, 1), [(0, (255, 255, 255)), (0.4, GOLD), (1, MAGENTA)]),
                     BORDER * np.clip(head + tail * 0.8, 0, 1))

        # holo foil (UR, LR): rainbow sheen inside a wide band of light sweeping across the card; keeping it
        # to a band (instead of the whole art) means far fewer changed pixels per frame, so smaller files
        if rank in ("UR", "LR"):
            hue = (XX * 0.8 + YY * 0.5) / 420 + t
            pos = -260 + (SW + SH * 0.5 + 520) * t
            band = np.exp(-((XX + YY * 0.5 - pos) / 170) ** 2)
            over(f, hsv(hue, 0.6, 1.0), ART_M * band * (0.22 if rank == "UR" else 0.16))

        # shine sweep over the card
        t0, t1 = {"R": (0.05, 0.55), "SR": (0.05, 0.5), "SSR": (0.1, 0.55), "UR": (0.15, 0.6), "LR": (0.2, 0.65)}[rank]
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0)
            colours = {"SSR": ((255, 255, 255), (255, 240, 180), GOLD), "SR": ((255, 255, 255), LILAC, MAGENTA)}.get(
                rank, ((255, 255, 255), ICE, LILAC, MAGENTA))
            band = np.asarray(shine_band((SW, SH), -300 + (SW + SH * 0.35 + 600) * u, 80, 0.35, colours=colours,
                                         strength=150), np.float32)
            over(f, band[..., :3], band[..., 3] / 255 * CARD)

        # text and ornaments on top
        over_img(f, top)

        # particles in front
        fx = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        d = ImageDraw.Draw(fx)
        for x, y, ph, s in twinkles:
            a = max(0.0, math.sin(2 * math.pi * (2 * t + ph)))
            if a > 0.05:
                sparkle(d, x, y, int(s * (0.6 + 0.4 * a)), LACE if rank != "SSR" else (255, 240, 190), int(255 * a))
        if rank == "SSR":  # gold glitter rising over the art
            for x, y0, spd, ph in glitter:
                y = M + CH - BW - ((y0 + t * spd) % 1) * (CH - 2 * BW)
                a = int(200 * (0.5 + 0.5 * math.sin(2 * math.pi * (3 * t + ph))))
                d.ellipse((x - 2.5, y - 2.5, x + 2.5, y + 2.5), fill=rgba(GOLD, a))
        if rank == "LR":  # petals and gold flecks drifting across the whole card
            cols = [(255, 170, 210), GOLD, (255, 240, 250)]
            for x0, y0, ph, ci in petals:
                y = (y0 + t) % 1 * (SH + 40) - 20
                x = (x0 - t * 120 + 18 * math.sin(2 * math.pi * (t + ph))) % SW
                ang = 2 * math.pi * (t * 2 + ph)
                pts = [(x + 9 * math.cos(ang + a_) * (1 if j % 2 == 0 else 0.45),
                        y + 9 * math.sin(ang + a_) * (1 if j % 2 == 0 else 0.45))
                       for j, a_ in enumerate((0, math.pi / 2, math.pi, 3 * math.pi / 2))]
                d.polygon(pts, fill=rgba(cols[ci], 230))
        if fx.getbbox():
            over_img(f, blur_glow(fx, 5, 1.4))
            over_img(f, fx)

        img = Image.fromarray(np.clip(np.dstack([f[..., :3], f[..., 3:4] * 255]), 0, 255).astype(np.uint8), "RGBA")
        frames.append(img)
    return frames


def card(key):
    """Two files from one render: the AniList-size card and a full-size one for the showcase site."""
    w = next(w for w in WAIFUS if w[0] == key)
    frames = card_frames(*w)
    out = RANKS[w[4]]["out"]
    small = [f.resize((out, round(out * SH / SW)), Image.LANCZOS) for f in frames]
    save_anim(small, f"{SUB}card-{key}.webp", [75] * len(frames), quality=80)
    save_anim(frames, f"{SUB}hd/card-{key}.webp", [75] * len(frames), quality=82)


def hex_(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c[:3])


def manifest():
    """profile/waifus/waifus.json: everything the showcase site needs, highest rank first."""
    ranked = sorted(WAIFUS, key=lambda w: -RANKS[w[4]]["level"])
    data = {
        "ranks": {rk: {"name": RANKS[rk]["name"], "level": RANKS[rk]["level"],
                       "colours": [hex_(c) for _, c in RANKS[rk]["stops"]], "glow": hex_(RANKS[rk]["glow"])}
                  for rk in sorted(RANKS, key=lambda k: -RANKS[k]["level"])},
        "waifus": [{"key": k, "name": name, "jp": jp, "series": series, "rank": rank,
                    "anilist": f"https://anilist.co/character/{ANILIST[k]}" if k in ANILIST else None,
                    "card": f"card-{k}.webp", "hd": f"hd/card-{k}.webp", "size": [SW, SH]}
                   for k, name, jp, series, rank in ranked],
    }
    path = OUT / SUB / "waifus.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"waifus.json: {len(data['waifus'])} waifus")


# ---------------------------------------------------------------- section header with the rank legend

def header():
    H = 420
    img = panel_base(H, bg="aurora", focus=(0.5, 0.3), dim=0.72)
    img.alpha_composite(particles(img.size, 50, 29, rmax=8, colours=(MAGENTA, MINT, GOLD, LACE)))
    section_title(img, 66, "CHARACTER FILES", "WAIFU COLLECTION", "俺の嫁",
                  stops=[(0, MAGENTA), (0.5, VIOLET), (1, MINT)], glow=MAGENTA, label_col=MAGENTA)
    # legend: badge + rank name + stars for each rank, left to right from LR down to R
    order = ["LR", "UR", "SSR", "SR", "R"]
    slot = (W - 120) / len(order)
    size = 30  # one size for all labels: the largest at which the longest still fits its slot
    while any(font("bahn", size, "Bold").getlength(RANKS[rk]["name"]) + 3 * len(RANKS[rk]["name"]) > slot - 30
              for rk in order):
        size -= 1
    for i, rk in enumerate(order):
        cx = 60 + slot * (i + 0.5)
        tmp = Image.new("RGBA", (300, 60), (0, 0, 0, 0))
        bw = rank_badge(tmp, 0, 4, rk, h=52)
        img.alpha_composite(tmp, (int(cx - bw / 2), 230))
        draw_text(img, (cx, 330), RANKS[rk]["name"], font("bahn", size, "Bold"), anchor="ms", tracking=3,
                  fill=mix(RANKS[rk]["stops"][0][1], LACE, 0.25) if rk not in ("UR", "LR") else LACE)
        lv = RANKS[rk]["level"]
        stars(img, int(cx - (lv - 1) * 30 / 2), 368, rk, size=11, gap=30)
    save(finish_card(img, stops=[(0, MAGENTA), (0.5, VIOLET), (1, MINT)], glow_col=MAGENTA), f"{SUB}waifu-head.webp")


if __name__ == "__main__":
    keys = sys.argv[1:]
    if not keys:
        header()
        keys = [w[0] for w in WAIFUS]
    for k in keys:
        if k == "header":
            header()
        elif k != "manifest":
            card(k)
    manifest()
