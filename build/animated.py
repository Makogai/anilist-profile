"""Animated assets: hero banner, holo waifu cards and the morning-star chain separator.

Animated WebP is used so they can be shown with img720 like the static panels (crisp 2x text).
Run: python build/animated.py [cards|row|chain|hero]
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from common import (ART, BLUE, black_to_alpha, CORAL, GOLD, ICE, INDIGO, LACE, LILAC, MAGENTA, OUT,
                    SATIN, VIOLET, VOID, W, blur_glow, card_frame, cover, diamond,
                    draw_text, finish_card, font, gradient, panel_base, rgba, ribbon_x, rounded_mask, screen,
                    sparkle, text_mask)


def save_anim(frames, name, durations, quality=80):
    path = OUT / name
    frames[0].save(path, "WEBP", save_all=True, append_images=frames[1:], duration=durations, loop=0,
                   quality=quality, method=6, minimize_size=True, allow_mixed=True,
                   kmin=len(frames) - 1, kmax=len(frames))
    print(f"{name}: {frames[0].size[0]}x{frames[0].size[1]}, {len(frames)} frames, "
          f"{path.stat().st_size / 1024:.0f} KB")


def shine_band(size, pos, width=110, angle=0.35, colours=((255, 255, 255), ICE, LILAC, MAGENTA),
               strength=150):
    """Diagonal holographic light band centred at x = pos (can be off-canvas)."""
    w, h = size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = (x + y * angle) - pos
    core = np.exp(-(d / width) ** 2)
    out = np.zeros((h, w, 4), np.float32)
    # rainbow-ish tint across the band
    t = np.clip((d / width + 1.5) / 3, 0, 1)
    cols = np.array(colours, np.float32)
    idx = t * (len(cols) - 1)
    lo = np.floor(idx).astype(int).clip(0, len(cols) - 2)
    f = (idx - lo)[..., None]
    out[..., :3] = cols[lo] * (1 - f) + cols[lo + 1] * f
    out[..., 3] = core * strength
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- waifu cards

CARDS = [
    ("rem", "REM", "レム", "RE:ZERO", [(0, ICE), (0.5, BLUE), (1, VIOLET)], BLUE, MAGENTA),
    ("zerotwo", "ZERO TWO", "ゼロツー", "DARLING IN THE FRANXX", [(0, CORAL), (0.5, MAGENTA), (1, VIOLET)],
     MAGENTA, CORAL),
    ("shiro", "SHIRO", "白", "NO GAME NO LIFE", [(0, LILAC), (0.5, VIOLET), (1, BLUE)], VIOLET, GOLD),
]


def card_still(key, name, jp, series, stops, glow, accent):
    cw, ch, m = 460, 690, 12
    img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    iw, ih = cw - 2 * m, ch - 2 * m
    art = cover(Image.open(ART / f"waifu-{key}.png").convert("RGBA"), (iw, ih), (0.5, 0.0))
    art.alpha_composite(gradient(iw, ih, [(0, (0, 0, 0, 0)), (0.6, (0, 0, 0, 0)), (0.78, rgba(VOID, 200)),
                                          (1, rgba(VOID, 250))], "v"))
    art.putalpha(rounded_mask((iw, ih), 26))
    img.alpha_composite(art, (m, m))
    img.alpha_composite(card_frame((cw, ch), 28, 4, stops, glow, inset=m - 2))
    d = ImageDraw.Draw(img)
    # rarity badge
    bx, by = 34, 34
    badge = gradient(92, 40, [(0, rgba(GOLD)), (1, rgba((255, 150, 80)))])
    badge.putalpha(rounded_mask((92, 40), 10))
    img.alpha_composite(badge, (bx, by))
    draw_text(img, (bx + 46, by + 21), "SSR", font("bahn", 28, "Bold"), fill=SATIN, anchor="mm",
              tracking=3, shadow=False)
    # JP name in a vertical rail on the right
    rail_x = cw - 58
    rail = Image.new("RGBA", (40, 40 + 46 * len(jp)), rgba(SATIN, 170))
    rail.putalpha(rounded_mask(rail.size, 12).point(lambda v: v * 170 // 255))
    img.alpha_composite(rail, (rail_x - 20, 30))
    for i, chr_ in enumerate(jp):
        draw_text(img, (rail_x, 70 + i * 46), chr_, font("serifjp", 34, "Bold"), fill=LACE,
                  anchor="mm", glow=glow, glow_radius=6, shadow=False)
    # labels
    draw_text(img, (36, 530), series, font("bahn", 29, "SemiBold"), fill=stops[0][1], anchor="ls",
              tracking=2, shadow=False)
    size = 76 if len(name) <= 5 else 62
    draw_text(img, (32, 604), name, font("bahn", size, "Bold"), anchor="ls", tracking=6,
              gradient_stops=[(0, LACE), (0.45, stops[0][1]), (1, stops[-1][1])], glow=glow, glow_radius=14)
    for i in range(5):
        diamond(d, 44 + i * 30, 640, 9, fill=rgba(GOLD))
    ribbon_x(d, cw - 50, 640, 11, accent, 5)
    return img


def cards():
    for key, *rest in CARDS:
        still = card_still(key, *rest)
        w, h = still.size
        mask = rounded_mask((w - 24, h - 24), 26)
        frames, durs = [still], [2600]
        n = 16
        for i in range(n):
            pos = -250 + (w + h * 0.35 + 500) * i / (n - 1)
            f = still.copy()
            band = shine_band((w - 24, h - 24), pos, 90)
            a = np.minimum(np.asarray(band.getchannel("A")), np.asarray(mask))
            band.putalpha(Image.fromarray(a, "L"))
            f.alpha_composite(band, (12, 12))
            frames.append(f)
            durs.append(45)
        save_anim(frames, f"waifu-{key}.webp", durs, quality=86)


def cards_row():
    """All three cards in one 1440 px row (they would not fit side by side as separate images in
    the ~514 px About column). The holo shine sweeps across them one after another."""
    stills = [card_still(key, *rest) for key, *rest in CARDS]
    cw, ch = stills[0].size
    sc = 0.94
    sw, sh = round(cw * sc), round(ch * sc)
    gap = (W - 3 * sw) // 4
    # the cards sit on an opaque night-sky card: transparent gaps between animated cards picked up
    # lossy-alpha smears in the WebP encoder
    bg = finish_card(panel_base(sh + 2 * gap, focus=(0.5, 0.3)))
    xs = [gap + i * (sw + gap) for i in range(3)]
    small = [s.resize((sw, sh), Image.LANCZOS) for s in stills]
    base = bg.copy()
    for x, s in zip(xs, small):
        base.alpha_composite(s, (x, gap))
    mask = np.asarray(rounded_mask((cw - 24, ch - 24), 26))
    sweep, stagger = 16, 7
    total = sweep + stagger * 2
    frames, durs = [base], [2600]
    for fi in range(total):
        f = bg.copy()  # redraw every card on the clean background so glows never stack
        for i in range(3):
            k = fi - i * stagger
            card = small[i]
            if 0 <= k < sweep:
                pos = -250 + (cw + ch * 0.35 + 500) * k / (sweep - 1)
                band = shine_band((cw - 24, ch - 24), pos, 90)
                band.putalpha(Image.fromarray(np.minimum(np.asarray(band.getchannel("A")), mask), "L"))
                card = stills[i].copy()
                card.alpha_composite(band, (12, 12))
                card = card.resize((sw, sh), Image.LANCZOS)
            f.alpha_composite(card, (xs[i], gap))
        frames.append(f)
        durs.append(45)
    save_anim(frames, "waifu-row.webp", durs, quality=84)


# ---------------------------------------------------------------- hero banner

HW, HH = W, 520


def hero_base():
    art = Image.open(ART / "hero-rem.png").convert("RGBA")
    img = cover(art, (HW, HH), (0.9, 0.47))
    img.alpha_composite(gradient(HW, HH, [(0, rgba(VOID, 200)), (0.45, rgba(VOID, 60)), (0.6, rgba(VOID, 0))]))
    lace = Image.open(ART / "orn-lace.png").convert("RGBA")
    band = lace.crop((0, 450, lace.width, 562)).resize((HW - 80, round(112 * (HW - 80) / lace.width)))
    screen(img, band, 0.9, (40, HH - band.height - 8))
    draw_text(img, (92, 128), "ANILIST  //  PROFILE", font("bahn", 34, "SemiBold"), fill=ICE,
              anchor="ls", tracking=10, shadow=False)
    name_font = font("bahn", 168, "Bold")
    draw_text(img, (84, 292), "MAKOGAI", name_font, anchor="ls", tracking=10,
              gradient_stops=[(0, LACE), (0.4, ICE), (1, VIOLET)], glow=BLUE, glow_radius=24,
              glow_strength=1.3)
    draw_text(img, (94, 360), "Male  •  Software Engineer", font("bahn", 50, "SemiBold"), fill=LACE,
              anchor="ls", tracking=2)
    tags = ["RE:ZERO DEVOTEE", "457 ANIME", "359 MANGA"]
    x = 94
    for t in tags:
        tf = font("bahn", 28, "SemiBold")
        width = int(sum(tf.getlength(c) for c in t) + 4 * (len(t) - 1)) + 40
        pill = Image.new("RGBA", (width, 54), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, width - 1, 53), 27, fill=rgba(INDIGO, 200),
                                               outline=rgba(ICE, 180), width=2)
        img.alpha_composite(pill, (x, 392))
        draw_text(img, (x + width // 2, 429), t, tf, fill=ICE, anchor="ms", tracking=4, shadow=False)
        x += width + 14
    d = ImageDraw.Draw(img)
    ribbon_x(d, 76, 166, 12, MAGENTA, 6)
    name_mask = text_mask((HW, HH), (84, 292), "MAKOGAI", name_font, "ls", 10)
    return img, name_mask


def hero_frames(fps, seconds):
    base, name_mask = hero_base()
    n = fps * seconds
    rng = np.random.default_rng(42)
    P = 70
    px = rng.uniform(0, HW, P)
    py = rng.uniform(0, HH, P)
    depth = rng.choice([1, 1, 1, 2], P)
    size = rng.uniform(1.5, 4.5, P) * depth
    phase = rng.uniform(0, 2 * math.pi, P)
    star = rng.random(P) < 0.25
    cols = [ICE, LACE, BLUE, LILAC]
    col = rng.integers(0, len(cols), P)
    moon = (862, 154)
    nm = np.asarray(name_mask, np.float32) / 255
    frames = []
    for i in range(n):
        t = i / n  # 0..1 loop phase
        f = base.copy()
        # moon breathing glow
        g = Image.new("RGBA", (HW, HH), (0, 0, 0, 0))
        r = 120 + 18 * math.sin(2 * math.pi * t)
        ImageDraw.Draw(g).ellipse((moon[0] - r, moon[1] - r, moon[0] + r, moon[1] + r),
                                  fill=rgba(ICE, int(40 + 25 * math.sin(2 * math.pi * t))))
        f.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
        # snow / sparkles: y wraps once (or twice for near flakes) per loop, x sways
        layer = Image.new("RGBA", (HW, HH), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for k in range(P):
            yy = (py[k] + t * (HH + 40) * depth[k]) % (HH + 40) - 20
            xx = px[k] + 26 * math.sin(2 * math.pi * t * depth[k] + phase[k])
            a = int(150 + 100 * math.sin(2 * math.pi * t * 2 + phase[k]))
            c = cols[col[k]]
            if star[k]:
                sparkle(d, xx, yy, int(size[k] * 3), c, a)
            else:
                d.ellipse((xx - size[k], yy - size[k], xx + size[k], yy + size[k]), fill=rgba(c, a))
        f.alpha_composite(blur_glow(layer, 5, 1.5))
        f.alpha_composite(layer)
        # shine sweep across the name in the first 40% of the loop
        if t < 0.4:
            pos = -300 + (1400 + 300) * (t / 0.4)
            band = np.asarray(shine_band((HW, HH), pos, 70, 0.3, strength=210), np.float32)
            band[..., 3] *= nm
            f.alpha_composite(Image.fromarray(band.astype(np.uint8), "RGBA"))
        frames.append(finish_card(f))
    return frames


def hero():
    frames = hero_frames(12, 6)
    save_anim(frames, "hero.webp", [83] * len(frames), quality=78)


# ---------------------------------------------------------------- chain separator

def chain():
    orn = Image.open(ART / "orn-morningstar.png").convert("RGB")
    band = orn.crop((0, 410, orn.width, 600)).resize((W, round(190 * W / orn.width)), Image.LANCZOS)
    h = band.height
    a = np.asarray(band, np.float32)
    lum = a.max(axis=2)
    xs = np.arange(W, dtype=np.float32)

    def frame(pulse_x, colour):
        # only the strip around the pulse changes, which keeps the animated WebP small
        pulse = np.exp(-((xs - pulse_x) / 55) ** 2) if pulse_x is not None else np.zeros(W)
        boost = (lum / 255)[..., None] * pulse[None, :, None] * 1.5
        return black_to_alpha(np.clip(a + np.array(colour, np.float32) * boost, 0, 255))

    # a light runs left to right along the chain, ice blue before the morning star, violet after
    n = 18
    frames, durs = [frame(None, ICE)], [1400]
    for i in range(n):
        x = -60 + (W + 120) * i / (n - 1)
        frames.append(frame(x, ICE if x < W / 2 else LILAC))
        durs.append(50)
    save_anim(frames, "sep-chain.webp", durs, quality=80)


if __name__ == "__main__":
    which = sys.argv[1:] or ["cards", "row", "chain", "hero"]
    for w_ in which:
        {"cards": cards, "row": cards_row, "chain": chain, "hero": hero}[w_]()
