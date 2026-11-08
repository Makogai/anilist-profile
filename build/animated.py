"""Animated assets (animated WebP, shown with img720 like the static panels, so text stays crisp):
hero banner and About me (living Rem: hair sway, blink, wave), waifu fan, crossing marquee tapes,
episode-milestone staircase and the chain separator.

Run: python build/animated.py [hero|intro|waifu|tapes|milestones|chain]
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import panels
from common import (ART, BLUE, CORAL, GOLD, GOLD_CORAL, ICE, LACE, LILAC, MAGENTA, MINT, OUT, RAINBOW, SATIN,
                    SILVER, VIOLET, VOID, W, black_to_alpha, blur_glow, card_finisher, card_frame,
                    chamfer_frame, chamfer_poly, cover, diamond, draw_text, finish_card, font, gradient,
                    gradient_map, load_stats, mix, panel_base, particles, rgba, ribbon_x, rotated, rounded_mask,
                    section_title, sparkle, text_mask)
from live import Animator, blend_eyes, blink_amount, ellipse_mask, hsv_mask, locate_change, to_np, to_pil


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
    t = np.clip((d / width + 1.5) / 3, 0, 1)  # rainbow-ish tint across the band
    cols = np.array(colours, np.float32)
    idx = t * (len(cols) - 1)
    lo = np.floor(idx).astype(int).clip(0, len(cols) - 2)
    f = (idx - lo)[..., None]
    out[..., :3] = cols[lo] * (1 - f) + cols[lo + 1] * f
    out[..., 3] = core * strength
    return Image.fromarray(out.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- waifu cards

CARDS = [  # key, name, Japanese name, series, frame gradient, glow, accent
    ("rem", "REM", "レム", "RE:ZERO", [(0, ICE), (0.5, BLUE), (1, VIOLET)], BLUE, MAGENTA),
    ("zerotwo", "ZERO TWO", "ゼロツー", "DARLING IN THE FRANXX", [(0, CORAL), (0.5, MAGENTA), (1, VIOLET)],
     MAGENTA, CORAL),
    ("iroha", "IROHA", "色葉", "3D KANOJO: REAL GIRL", [(0, MINT), (0.5, BLUE), (1, VIOLET)], MINT, GOLD),
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
    bx, by = 34, 34  # rarity badge
    badge = gradient(92, 40, [(0, rgba(GOLD)), (1, rgba((255, 150, 80)))])
    badge.putalpha(rounded_mask((92, 40), 10))
    img.alpha_composite(badge, (bx, by))
    draw_text(img, (bx + 46, by + 21), "SSR", font("bahn", 28, "Bold"), fill=SATIN, anchor="mm",
              tracking=3, shadow=False)
    rail_x = cw - 58  # Japanese name in a vertical rail on the right
    rail = Image.new("RGBA", (40, 40 + 46 * len(jp)), rgba(SATIN, 170))
    rail.putalpha(rounded_mask(rail.size, 12).point(lambda v: v * 170 // 255))
    img.alpha_composite(rail, (rail_x - 20, 30))
    for i, chr_ in enumerate(jp):
        draw_text(img, (rail_x, 70 + i * 46), chr_, font("serifjp", 34, "Bold"), fill=LACE,
                  anchor="mm", glow=glow, glow_radius=6, shadow=False)
    draw_text(img, (36, 530), series, font("bahn", 29, "SemiBold"), fill=stops[0][1], anchor="ls",
              tracking=2, shadow=False)
    size = 76 if len(name) <= 5 else 62
    draw_text(img, (32, 604), name, font("bahn", size, "Bold"), anchor="ls", tracking=6,
              gradient_stops=[(0, LACE), (0.45, stops[0][1]), (1, stops[-1][1])], glow=glow, glow_radius=14)
    for i in range(5):
        diamond(d, 44 + i * 30, 640, 9, fill=rgba(GOLD))
    ribbon_x(d, cw - 50, 640, 11, accent, 5)
    return img


WAIFU_STOPS = [(0, MAGENTA), (0.5, VIOLET), (1, MINT)]


def waifu():
    """Section title + a fanned hand of cards (Rem raised in the middle); a holo shine sweeps
    left -> centre -> right. Cards sit on an opaque card: transparent gaps around animated cards
    picked up lossy-alpha smears in the WebP encoder."""
    H = 1090
    bg = panel_base(H, bg="aurora", focus=(0.5, 0.7), dim=0.72)
    glow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((420, 300, 1020, 980), fill=rgba(BLUE, 90))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(100)))
    bg.alpha_composite(particles(bg.size, 60, 29, rmax=9, colours=(MAGENTA, MINT, ICE, LACE)))
    section_title(bg, 66, "CHARACTER FILES", "WAIFU COLLECTION", "俺の嫁", stops=WAIFU_STOPS, glow=MAGENTA,
                  label_col=MAGENTA)
    # "best girl" tag under Rem
    tf = font("bahn", 30, "Bold")
    tw = int(tf.getlength("BEST GIRL") + 5 * 8 + 90)
    tag = gradient(tw, 52, [(0, rgba(GOLD)), (1, rgba(CORAL))])
    tag.putalpha(rounded_mask((tw, 52), 26))
    bg.alpha_composite(tag, (720 - tw // 2, 990))
    draw_text(bg, (720, 1026), "BEST GIRL", tf, fill=SATIN, anchor="ms", tracking=5, shadow=False)
    dd = ImageDraw.Draw(bg)
    for sx in (720 - tw // 2 + 26, 720 + tw // 2 - 26):
        diamond(dd, sx, 1016, 8, fill=rgba(SATIN))
    bg = finish_card(bg, stops=WAIFU_STOPS, glow_col=MAGENTA)

    stills = {key: card_still(key, *rest) for key, *rest in CARDS}
    # key, scale, tilt, centre; drawn in this order so Rem ends up on top
    layout = [("zerotwo", 0.86, 8, (274, 650)), ("iroha", 0.86, -8, (1166, 650)), ("rem", 1.0, 0, (720, 620))]
    shine_order = {"zerotwo": 0, "rem": 1, "iroha": 2}

    def place(card, scale, tilt):
        c = card.resize((round(card.width * scale), round(card.height * scale)), Image.LANCZOS)
        return rotated(c, tilt) if tilt else c

    static = {k: place(stills[k], s, a) for k, s, a, _ in layout}
    cw, ch = 460, 690
    mask = np.asarray(rounded_mask((cw - 24, ch - 24), 26))
    sweep, stagger = 16, 8
    frames, durs = [], []
    for fi in [-1] + list(range(sweep + 2 * stagger)):
        f = bg.copy()
        for key, scale, tilt, (cx, cy) in layout:
            img = static[key]
            k = fi - shine_order[key] * stagger
            if fi >= 0 and 0 <= k < sweep:
                pos = -250 + (cw + ch * 0.35 + 500) * k / (sweep - 1)
                band = shine_band((cw - 24, ch - 24), pos, 90)
                band.putalpha(Image.fromarray(np.minimum(np.asarray(band.getchannel("A")), mask), "L"))
                card = stills[key].copy()
                card.alpha_composite(band, (12, 12))
                img = place(card, scale, tilt)
            f.alpha_composite(img, (cx - img.width // 2, cy - img.height // 2))
        frames.append(f)
        durs.append(2600 if fi < 0 else 45)
    save_anim(frames, "waifu.webp", durs, quality=84)


# ---------------------------------------------------------------- living Rem helpers

def eye_mask_from(base: np.ndarray, blink: np.ndarray, pad=18, blur=7):
    """Feathered ellipse over the eye, located where the closed-eye art differs from the original."""
    x0, y0, x1, y1, _, _ = locate_change(base, blink)
    return ellipse_mask(base.shape, ((x0 + x1) / 2, (y0 + y1) / 2), ((x1 - x0) / 2 + pad, (y1 - y0) / 2 + pad),
                        blur)


def ramp(values, lo, hi):
    """0 below lo, 1 above hi, smooth in between (for limiting masks to a region)."""
    return np.clip((values - lo) / max(hi - lo, 1e-6), 0, 1)


def mask_centre(anim, mask):
    return anim.xx[mask > 0.5].mean(), anim.yy[mask > 0.5].mean()


# ---------------------------------------------------------------- hero banner

HW, HH = W, 520
NAME_XY = (84, 318)
HERO_FRAME = [(0, ICE), (0.5, VIOLET), (1, MAGENTA)]


def hero_layers():
    """Rem art (and its closed-eye twin) cropped to the hero, plus an overlay with everything above it."""
    art = to_np(cover(Image.open(ART / "hero-rem.png").convert("RGBA"), (HW, HH), (0.9, 0.47)))
    blink = to_np(cover(Image.open(ART / "hero-rem-blink.png").convert("RGBA"), (HW, HH), (0.9, 0.47)))
    over = gradient(HW, HH, [(0, rgba(VOID, 200)), (0.45, rgba(VOID, 60)), (0.6, rgba(VOID, 0))])
    lace = Image.open(ART / "orn-lace.png").convert("RGB")
    band = lace.crop((0, 450, lace.width, 562)).resize((HW - 80, round(112 * (HW - 80) / lace.width)))
    over.alpha_composite(black_to_alpha(np.asarray(band, np.float32)), (40, HH - band.height - 8))
    draw_text(over, (92, 152), "ANILIST  //  PROFILE", font("bahn", 34, "SemiBold"), fill=ICE,
              anchor="ls", tracking=10, shadow=False)
    name_font = font("bahn", 168, "Bold")
    draw_text(over, NAME_XY, "MAKOGAI", name_font, anchor="ls", tracking=10,
              gradient_stops=[(0, LACE), (0.35, ICE), (0.7, VIOLET), (1, MAGENTA)], glow=BLUE, glow_radius=24,
              glow_strength=1.3)
    sub_f = font("bahn", 50, "SemiBold")
    x, y = 94, 396
    draw_text(over, (x, y), "Male", sub_f, fill=LACE, anchor="ls", tracking=2)
    x += sub_f.getlength("Male") + 2 * 3 + 30
    diamond(ImageDraw.Draw(over), x, y - 18, 10, fill=rgba(MAGENTA))
    draw_text(over, (x + 30, y), "Software Engineer", sub_f, anchor="ls", tracking=2,
              gradient_stops=[(0, LACE), (1, MINT)])
    ribbon_x(ImageDraw.Draw(over), 76, 190, 12, MAGENTA, 6)
    return art, blink, over, text_mask((HW, HH), NAME_XY, "MAKOGAI", name_font, "ls", 10)


def hero_frames(fps, seconds):
    art, blink, over, name_mask = hero_layers()
    eye = eye_mask_from(art, blink)
    anim = Animator(art)
    rgb = art[..., :3]
    moon = (862, 154)
    not_moon = 1 - ellipse_mask(art.shape, moon, (150, 150), 20)
    not_eye = 1 - ellipse_mask(art.shape, mask_centre(anim, eye), (70, 50), 10)
    hair = hsv_mask(rgb, (195, 235), 0.35, 0.42, 4) * ramp(anim.xx, 900, 960) * not_moon * not_eye
    ribbon = hsv_mask(rgb, (300, 345), 0.3, 0.35, 4) * ramp(anim.xx, 1220, 1250)
    finish = card_finisher((HW, HH), stops=HERO_FRAME)
    n = fps * seconds
    rng = np.random.default_rng(42)
    P = 70
    px = rng.uniform(0, HW, P)
    py = rng.uniform(0, HH, P)
    depth = rng.choice([1, 1, 1, 2], P)
    size = rng.uniform(1.5, 4.5, P) * depth
    phase = rng.uniform(0, 2 * math.pi, P)
    star = rng.random(P) < 0.25
    cols = [ICE, LACE, MAGENTA, MINT]
    col = rng.integers(0, len(cols), P)
    nm = np.asarray(name_mask, np.float32) / 255
    frames = []
    for i in range(n):
        t = i / n  # 0..1 loop phase
        anim.sway(hair, 2 * t, 3.2, wavelength=140)
        anim.sway(ribbon, 3 * t + 0.25, 4.5, wavelength=80)
        f = to_pil(blend_eyes(anim.render(), blink, eye, blink_amount(t, 0.62)))
        f.alpha_composite(over)
        g = Image.new("RGBA", (HW, HH), (0, 0, 0, 0))  # moon breathing glow
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
        if t < 0.4:  # shine sweep across the name in the first 40% of the loop
            pos = -300 + (1400 + 300) * (t / 0.4)
            band = np.asarray(shine_band((HW, HH), pos, 70, 0.3, strength=210), np.float32)
            band[..., 3] *= nm
            f.alpha_composite(Image.fromarray(band.astype(np.uint8), "RGBA"))
        frames.append(finish(f))
    return frames


def hero():
    frames = hero_frames(12, 6)
    save_anim(frames, "hero.webp", [83] * len(frames), quality=78)


# ---------------------------------------------------------------- about me: Rem waves, blinks, hair sways

def intro():
    bg, over = panels.intro_layers()
    rem, pos = panels.intro_rem()
    a = to_np(rem)
    blink = to_np(panels.intro_rem("intro-rem-blink.png")[0])
    fade = panels.intro_fade(rem.size)
    eye = eye_mask_from(a, blink)
    anim = Animator(a)
    not_eye = 1 - ellipse_mask(a.shape, mask_centre(anim, eye), (80, 60), 10)
    hair = hsv_mask(a[..., :3], (195, 235), 0.35, 0.42, 4) * (1 - ramp(anim.yy, 560, 640)) * not_eye
    ribbon = hsv_mask(a[..., :3], (300, 345), 0.3, 0.4, 4) * ramp(anim.xx, 630, 660)
    hand = ellipse_mask(a.shape, (165, 640), (125, 165), 22)
    wrist = (237, 787)
    finish = card_finisher(bg.size, stops=panels.INTRO_FRAME)
    n = 48  # 4 s at 12 fps
    frames = []
    for i in range(n):
        t = i / n
        anim.sway(hair, t, 3.0, wavelength=150)
        anim.sway(ribbon, 2 * t + 0.3, 4.5, wavelength=90)
        anim.rotate(hand, wrist, 7 * math.sin(2 * math.pi * 3 * t))  # three waves per loop
        fr = blend_eyes(anim.render(), blink, eye, blink_amount(t, 0.7))
        fr[..., 3] = fade
        f = bg.copy()
        f.alpha_composite(to_pil(fr), pos)
        f.alpha_composite(over)
        frames.append(finish(f))
    save_anim(frames, "intro.webp", [83] * n, quality=80)


# ---------------------------------------------------------------- crossing marquee tapes

def tape_strip(words, text_col, spark_col, th):
    """One repeat period of tape text: words separated by drawn sparkles."""
    pieces, widths = [], []
    for wd in words:
        f = font("sansjp", 40, "Black") if any(ord(c) >= 0x3000 for c in wd) else font("bahn", 46, "Bold")
        wlen = int(f.getlength(wd) + 4 * (len(wd) - 1)) + 40
        pieces.append((wd, f, wlen))
        widths.append(wlen + 70)
    period = sum(widths)
    strip = Image.new("RGBA", (period, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    x = 0
    for (wd, f, wlen), wtot in zip(pieces, widths):
        draw_text(strip, (x + 20, th // 2 + 2), wd, f, fill=text_col, anchor="lm", tracking=4, shadow=False)
        sparkle(d, x + wlen + 35, th // 2, 18, spark_col)
        x += wtot
    return strip, period


def tapes():
    H, th, L = 300, 82, 1640
    specs = [  # words, tape gradient, text colour, sparkle colour, tilt, direction
        (["REM", "レム", "BEST GIRL", "鬼がかってますね"], [(0, MAGENTA), (0.5, VIOLET), (1, MAGENTA)], LACE, GOLD, -4.5, 1),
        (["WELCOME", "ようこそ", "MAKOGAI", "ANIME FOREVER"], [(0, ICE), (0.5, MINT), (1, ICE)], VOID, MAGENTA, 4.0, -1),
    ]
    prepared = []
    for words, stops, tcol, scol, tilt, direction in specs:
        strip, period = tape_strip(words, tcol, scol, th)
        reps = math.ceil((L + period) / period) + 1
        long = Image.new("RGBA", (period * reps, th), (0, 0, 0, 0))
        for i in range(reps):
            long.alpha_composite(strip, (i * period, 0))
        body = gradient(L, th, stops)
        edge = ImageDraw.Draw(body)
        edge.rectangle((0, 0, L, 5), fill=rgba(LACE, 120))
        edge.rectangle((0, th - 6, L, th), fill=rgba(VOID, 90))
        prepared.append((long, period, body, tilt, direction))
    n = 30
    frames = []
    for i in range(n):
        f = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for long, period, body, tilt, direction in prepared:
            off = int(period * i / n) if direction > 0 else int(period * (n - i) / n) % period
            t = body.copy()
            t.alpha_composite(long.crop((off, 0, off + L, th)))
            r = rotated(t, tilt)
            shadow = Image.new("RGBA", r.size, (0, 0, 0, 0))
            shadow.putalpha(r.getchannel("A").point(lambda v: v * 120 // 255))
            shadow = shadow.filter(ImageFilter.GaussianBlur(10))
            pos = (W // 2 - r.width // 2, H // 2 - r.height // 2)
            f.alpha_composite(shadow, (pos[0], pos[1] + 10))
            f.alpha_composite(r, pos)
        frames.append(f)
    save_anim(frames, "tapes.webp", [60] * n, quality=80)


# ---------------------------------------------------------------- episode milestones

TIERS = [  # episodes, tier name, crest colour ramp (None = prismatic), accent colour
    (1000, "BRONZE", [(0, (30, 15, 8)), (0.4, (140, 75, 35)), (0.7, (215, 140, 80)), (1, (255, 225, 190))],
     (232, 150, 92)),
    (2500, "SILVER", [(0, (20, 24, 34)), (0.4, (110, 120, 140)), (0.7, (195, 205, 222)), (1, (255, 255, 255))],
     (205, 214, 232)),
    (5000, "GOLD", [(0, (35, 22, 4)), (0.4, (175, 120, 25)), (0.7, (250, 200, 90)), (1, (255, 248, 215))],
     GOLD),
    (7500, "PLATINUM", [(0, (10, 25, 40)), (0.4, (70, 150, 200)), (0.7, (160, 230, 255)), (1, (255, 255, 255))],
     ICE),
    (10000, "DIAMOND", None, MAGENTA),
    (15000, "MYTHIC", [(0, (30, 8, 30)), (0.4, (150, 40, 120)), (0.7, (240, 110, 200)), (1, (255, 225, 245))],
     CORAL),
    (20000, "LEGEND", None, GOLD),
]


def milestone_window(episodes):
    """The five tiers to show: they end at the first tier not reached yet (or the last five)."""
    k = next((i for i, t in enumerate(TIERS) if t[0] > episodes), len(TIERS) - 1)
    start = min(max(0, k - 4), len(TIERS) - 5)
    return TIERS[start:start + 5]
MS_CARD = (300, 470)


def crest(ramp, size=230):
    rgb = np.asarray(Image.open(ART / "crest.png").convert("RGB").resize((size, size), Image.LANCZOS), np.float32)
    if ramp is not None:
        return gradient_map(rgb, ramp)
    # prismatic: white-metal ramp tinted by a diagonal rainbow
    img = gradient_map(rgb, [(0, (20, 20, 30)), (0.5, (170, 170, 190)), (1, (255, 255, 255))])
    a = np.asarray(img, np.float32)
    rb = np.asarray(gradient(size, size, [(0, (255, 120, 150)), (0.3, GOLD), (0.55, MINT), (0.8, BLUE), (1, VIOLET)],
                             "d"), np.float32)
    a[..., :3] = np.clip(a[..., :3] * (0.35 + 0.85 * rb[..., :3] / 255), 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def milestone_card(eps, tier, ramp, col, episodes):
    w, h = MS_CARD
    locked = eps > episodes
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    body = gradient(w, h, [(0, rgba(mix(col, VOID, 0.62 if not locked else 0.8), 250)), (1, rgba(VOID, 252))], "v")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(chamfer_poly(w, h, 26), fill=255)
    body.putalpha(m)
    img.alpha_composite(body)
    c = crest(ramp)
    if locked:
        a = np.asarray(c, np.float32)
        grey = a[..., :3].mean(axis=2, keepdims=True)
        a[..., :3] = (a[..., :3] * 0.45 + grey * 0.55) * 0.55
        c = Image.fromarray(a.astype(np.uint8), "RGBA")
    img.alpha_composite(c, (w // 2 - 115, 18))
    if locked:
        draw_text(img, (w // 2, 140), "", font("icons", 74), fill=LACE, anchor="mm", glow=MAGENTA,
                  glow_radius=14, shadow=False)
    draw_text(img, (w // 2, 290), tier, font("bahn", 30, "Bold"), fill=col, anchor="ms", tracking=8, shadow=False)
    draw_text(img, (w // 2, 368), f"{eps:,}", font("bahn", 78, "Bold Condensed"), anchor="ms",
              gradient_stops=[(0, LACE), (1, col)], glow=col, glow_radius=12)
    if not locked:
        draw_text(img, (w // 2, 406), "EPISODES", font("bahn", 27, "SemiBold"), fill=SILVER, anchor="ms",
                  tracking=6, shadow=False)
        uf = font("bahn", 24, "Bold")
        uw = uf.getlength("UNLOCKED") + 3 * 7
        draw_text(img, (w // 2 + 16, 446), "UNLOCKED", uf, fill=col, anchor="ms", tracking=3, shadow=False)
        draw_text(img, (w // 2 + 16 - uw / 2 - 18, 444), "", font("icons", 22), fill=col, anchor="ms",
                  shadow=False)
    else:
        bx0, bx1, by = 34, w - 34, 392
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((bx0, by, bx1, by + 16), 8, fill=rgba(SILVER, 50))
        frac = episodes / eps
        bar = gradient(int((bx1 - bx0) * frac), 16, RAINBOW)
        bar.putalpha(rounded_mask(bar.size, 8))
        img.alpha_composite(blur_glow(bar, 6, 1.4), (bx0, by))
        img.alpha_composite(bar, (bx0, by))
        draw_text(img, (w // 2, 446), f"{episodes:,} / {eps:,}  ·  {int(frac * 100)}%", font("bahn", 23, "Bold"),
                  fill=LACE, anchor="ms", tracking=2, shadow=False)
    stops = [(0, mix(col, LACE, 0.4)), (1, col)] if not locked else RAINBOW
    img.alpha_composite(chamfer_frame((w, h), 30, stops, col, inset=3, width=4))
    return img


def milestones():
    """Episode count from data/stats.json, refreshed daily by the GitHub Action."""
    episodes = load_stats()["anime"]["episodes"]
    tiers = milestone_window(episodes)
    H = 1120
    bg = panel_base(H, bg="night", focus=(0.3, 0.7), dim=0.9)
    bg.alpha_composite(particles(bg.size, 60, 41, rmax=8, colours=(GOLD, CORAL, LACE, ICE)))
    section_title(bg, 66, "ACHIEVEMENTS", "EPISODE MILESTONES", "視聴記録", x=90, align="l", jp_on_label=True,
                  stops=GOLD_CORAL, glow=CORAL, label_col=GOLD)
    w, h = MS_CARD
    xs = [44, 310, 576, 842, 1108]
    tops = [610, 522, 434, 346, 258]
    tilts = [-3, 2, -2, 3, -3]
    cards = [milestone_card(*t, episodes) for t in tiers]
    # progress trail floating above the cards: reached part in gold, the rest dashed
    pts = [(x + w // 2, t - 54) for x, t in zip(xs, tops)]
    j = sum(t[0] <= episodes for t in tiers)  # index of the first locked card (5 = all reached)
    if j == len(tiers):
        here = pts[-1]
        done = list(pts)
    else:
        prev_thr = tiers[j - 1][0] if j else 0
        seg = (episodes - prev_thr) / (tiers[j][0] - prev_thr)
        a_ = pts[j - 1] if j else (pts[0][0] - 120, pts[0][1] + 40)
        here = (a_[0] + (pts[j][0] - a_[0]) * seg, a_[1] + (pts[j][1] - a_[1]) * seg)
        done = pts[:j] + [here]
    trail = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(trail)
    if len(done) > 1:
        td.line(done, fill=rgba(GOLD), width=7, joint="curve")
    steps = 12
    for p0, p1 in zip([here] + pts[j:], pts[j:]):  # dashes from "you are here" through the locked tiers
        for i in range(0, steps, 2):
            a = (p0[0] + (p1[0] - p0[0]) * i / steps, p0[1] + (p1[1] - p0[1]) * i / steps)
            b = (p0[0] + (p1[0] - p0[0]) * (i + 1) / steps, p0[1] + (p1[1] - p0[1]) * (i + 1) / steps)
            td.line((a, b), fill=rgba(SILVER, 140), width=5)
    bg.alpha_composite(blur_glow(trail, 8, 1.6))
    bg.alpha_composite(trail)
    nd = ImageDraw.Draw(bg)
    for i, ((px, py), (_, _, _, col)) in enumerate(zip(pts, tiers)):
        if i < j:
            diamond(nd, px, py, 13, fill=rgba(col), outline=rgba(LACE), width=2)
        else:
            diamond(nd, px, py, 13, fill=rgba(VOID), outline=rgba(MAGENTA), width=3)
    for c, x, t, a in zip(cards, xs, tops, tilts):
        r = rotated(c, a)
        bg.alpha_composite(r, (x + w // 2 - r.width // 2, t + h // 2 - r.height // 2))
    bg = finish_card(bg, radius=30, stops=GOLD_CORAL, shape="chamfer", glow_col=CORAL)

    # animation: a spark runs along the finished trail, the "you are here" ring pulses,
    # and a prismatic shimmer crosses the locked card
    lens = [math.dist(done[i], done[i + 1]) for i in range(len(done) - 1)]
    total = sum(lens)

    def along(s):
        for (a, b), ln in zip(zip(done, done[1:]), lens):
            if s <= ln:
                return a[0] + (b[0] - a[0]) * s / ln, a[1] + (b[1] - a[1]) * s / ln
            s -= ln
        return done[-1]

    shimmer_i = min(j, len(tiers) - 1)  # the next tier to reach shimmers (the last one once all are reached)
    locked_card = cards[shimmer_i]
    lmask = Image.new("L", locked_card.size, 0)
    ImageDraw.Draw(lmask).polygon(chamfer_poly(*locked_card.size, 26), fill=255)
    n = 26
    frames = []
    for i in range(n):
        t = i / n
        f = bg.copy()
        fx = Image.new("RGBA", f.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(fx)
        if t < 0.7:
            sx, sy = along(total * t / 0.7)
            d.ellipse((sx - 14, sy - 14, sx + 14, sy + 14), fill=rgba(LACE))
        rr = 16 + 30 * ((t * 2) % 1)
        d.ellipse((here[0] - rr, here[1] - rr, here[0] + rr, here[1] + rr), outline=rgba(GOLD, int(255 * (1 - (t * 2) % 1))),
                  width=4)
        d.ellipse((here[0] - 11, here[1] - 11, here[0] + 11, here[1] + 11), fill=rgba(GOLD))
        f.alpha_composite(blur_glow(fx, 7, 1.6))
        f.alpha_composite(fx)
        if 0.3 <= t < 0.9:
            card = locked_card.copy()
            band = shine_band(card.size, -200 + (card.width + card.height * 0.35 + 400) * (t - 0.3) / 0.6, 70,
                              colours=((255, 255, 255), GOLD, MINT, MAGENTA), strength=120)
            band.putalpha(Image.fromarray(np.minimum(np.asarray(band.getchannel("A")), np.asarray(lmask)), "L"))
            card.alpha_composite(band)
            r = rotated(card, tilts[shimmer_i])
            f.alpha_composite(r, (xs[shimmer_i] + w // 2 - r.width // 2, tops[shimmer_i] + h // 2 - r.height // 2))
            for c, x, tp, a in list(zip(cards, xs, tops, tilts))[shimmer_i + 1:]:  # keep later cards on top
                r = rotated(c, a)
                f.alpha_composite(r, (x + w // 2 - r.width // 2, tp + h // 2 - r.height // 2))
        frames.append(f)
    save_anim(frames, "milestones.webp", [70] * n, quality=80)


# ---------------------------------------------------------------- chain separator

def chain():
    orn = Image.open(ART / "orn-morningstar.png").convert("RGB")
    band = orn.crop((0, 410, orn.width, 600)).resize((W, round(190 * W / orn.width)), Image.LANCZOS)
    a = np.asarray(band, np.float32)
    lum = a.max(axis=2)
    xs = np.arange(W, dtype=np.float32)

    def frame(pulse_x, colour):
        # only the strip around the pulse changes, which keeps the animated WebP small
        pulse = np.exp(-((xs - pulse_x) / 55) ** 2) if pulse_x is not None else np.zeros(W)
        boost = (lum / 255)[..., None] * pulse[None, :, None] * 1.5
        return black_to_alpha(np.clip(a + np.array(colour, np.float32) * boost, 0, 255))

    # a light runs left to right along the chain, ice blue before the morning star, pink after
    n = 18
    frames, durs = [frame(None, ICE)], [1400]
    for i in range(n):
        x = -60 + (W + 120) * i / (n - 1)
        frames.append(frame(x, ICE if x < W / 2 else MAGENTA))
        durs.append(50)
    save_anim(frames, "sep-chain.webp", durs, quality=80)


if __name__ == "__main__":
    jobs = {"hero": hero, "intro": intro, "waifu": waifu, "tapes": tapes, "milestones": milestones,
            "chain": chain}
    for name in sys.argv[1:] or list(jobs):
        jobs[name]()
