"""Static profile panels (WebP, 1440 px wide).

AniList shows the About column ~514 css px wide (measured), so text is sized to stay
readable at ~0.36x.

Run: python build/panels.py   (needs build/covers from build/fetch_covers.py)
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from common import (ART, BLUE, black_to_alpha, COVERS, GOLD, ICE, ICE_VIOLET, INDIGO, LACE,
                    LILAC, MAGENTA, SATIN, SILVER, VIOLET, VOID, W, blur_glow, card_frame,
                    cover, diamond, draw_rich, draw_text, finish_card, font, gradient, mix,
                    panel_base, particles, rgba, ribbon_x, rounded_mask, save, screen, sparkle)


# ---------------------------------------------------------------- shared pieces

def section_title(img, y, label, title, jp, x=None, align="m", rule=True, jp_on_label=False):
    """Small tracked label, big gradient title with glow, Japanese accent beside it."""
    cx = W // 2 if x is None else x
    anchor = "m" if align == "m" else "l"
    lb = draw_text(img, (cx, y), label, font("bahn", 32, "SemiBold"), fill=ICE, anchor=anchor + "s",
                   tracking=8, shadow=False)
    tx = cx
    if jp and not jp_on_label and align == "m":
        # centre title + Japanese accent as one group, not the title alone
        tx = cx - (24 + font("serifjp", 44, "Bold").getlength(jp)) / 2
    bbox = draw_text(img, (tx, y + 92), title, font("bahn", 86, "Bold"), anchor=anchor + "s",
                     tracking=6, gradient_stops=ICE_VIOLET, glow=BLUE, glow_radius=16,
                     glow_strength=1.1)
    if jp and jp_on_label:
        draw_text(img, (lb[2] + 28, y + 2), jp, font("serifjp", 36, "Bold"), fill=LILAC, anchor="ls",
                  glow=VIOLET, glow_radius=8)
    elif jp:
        draw_text(img, (bbox[2] + 24, y + 88), jp, font("serifjp", 44, "Bold"), fill=LILAC, anchor="ls",
                  glow=VIOLET, glow_radius=10)
    ry = y + 124
    if not rule:
        return ry
    # rule: gradient line with a diamond
    d = ImageDraw.Draw(img)
    if align == "m":
        x0, x1 = cx - 260, cx + 260
    else:
        x0, x1 = cx, cx + 520
    line = gradient(x1 - x0, 3, [(0, rgba(BLUE, 0)), (0.5, rgba(ICE, 255)), (1, rgba(VIOLET, 0))]) \
        if align == "m" else gradient(x1 - x0, 3, [(0, rgba(ICE, 255)), (1, rgba(VIOLET, 0))])
    img.alpha_composite(line, (x0, ry))
    mx = cx if align == "m" else x0 + 40
    diamond(d, mx, ry + 1, 9, fill=rgba(VOID), outline=rgba(ICE), width=3)
    return ry + 20


def glass(img, box, tint=BLUE, radius=28, alpha=150):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = gradient(w, h, [(0, rgba(INDIGO, alpha)), (1, rgba(VOID, alpha + 40))], "v")
    shine = gradient(w, h, [(0, rgba(tint, 60)), (0.35, rgba(tint, 0))], "d")
    layer.alpha_composite(shine)
    layer.putalpha(Image.fromarray(np.minimum(np.asarray(layer.getchannel("A")),
                                              np.asarray(rounded_mask((w, h), radius))), "L"))
    img.alpha_composite(layer, (x0, y0))
    border = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((0, 0, w - 1, h - 1), radius, outline=rgba(tint, 200), width=3)
    img.alpha_composite(blur_glow(border, 8, 1.2), (x0, y0))
    img.alpha_composite(border, (x0, y0))


def framed_cover(src, size, stops, glow_col, radius=26, focus=(0.5, 0.3)):
    """Cover art clipped to a rounded rect with a glowing gradient frame (returns padded RGBA)."""
    w, h = size
    pad = 30
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    art = cover(Image.open(src).convert("RGBA"), size, focus)
    shade = gradient(w, h, [(0, (0, 0, 0, 0)), (0.62, (0, 0, 0, 0)), (1, rgba(VOID, 235))], "v")
    art.alpha_composite(shade)
    art.putalpha(rounded_mask(size, radius))
    ring = Image.new("L", out.size, 0)
    ImageDraw.Draw(ring).rounded_rectangle((pad - 4, pad - 4, pad + w + 3, pad + h + 3), radius + 4,
                                           outline=255, width=5)
    glow = Image.new("RGBA", out.size, rgba(glow_col))
    glow.putalpha(ring)
    out.alpha_composite(blur_glow(glow, 16, 2.2))
    out.alpha_composite(art, (pad, pad))
    g = gradient(out.width, out.height, stops, "d")
    g.putalpha(ring)
    out.alpha_composite(g)
    return out, pad


def arc_gauge(img, c, r, value, stops, width=14, label=None):
    """Ring gauge for a 0-100 score."""
    x, y = c
    d = ImageDraw.Draw(img)
    d.ellipse((x - r, y - r, x + r, y + r), outline=rgba(SILVER, 50), width=width)
    seg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(seg)
    steps = int(360 * value / 100)
    for i in range(steps):
        t = i / 360
        col = mix(stops[0], stops[1], t)
        sd.arc((x - r, y - r, x + r, y + r), -90 + i, -89 + i + 1, fill=rgba(col), width=width)
    img.alpha_composite(blur_glow(seg, 8, 1.3))
    img.alpha_composite(seg)
    draw_text(img, (x, y + 6), f"{value:.1f}", font("bahn", 52, "Bold Condensed"), anchor="mm",
              fill=LACE, shadow=False)
    if label:
        draw_text(img, (x, y + r + 34), label, font("bahn", 28, "SemiBold"), fill=SILVER,
                  anchor="mm", tracking=4, shadow=False)


# ---------------------------------------------------------------- intro

def intro():
    H = 1180
    img = panel_base(H, focus=(0.2, 0.5))
    # Rem on the right, faded into the card
    rem = Image.open(ART / "intro-rem.png").convert("RGBA")
    rh = 1280
    rem = rem.resize((round(rem.width * rh / rem.height), rh), Image.LANCZOS)
    m = np.ones((rem.height, rem.width), np.float32)
    fx = np.clip(np.linspace(0, 1, rem.width) / 0.12, 0, 1)
    fy = np.clip((np.linspace(1, 0, rem.height)) / 0.25, 0, 1)
    ft = np.clip(np.linspace(0, 1, rem.height) / 0.06, 0, 1)
    m *= fx[None, :] * fy[:, None] * ft[:, None]
    rem.putalpha(Image.fromarray((m * 255).astype(np.uint8), "L"))
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse((900, 80, 1420, 600), fill=rgba(VIOLET, 90))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(90)))
    img.alpha_composite(rem, (W - rem.width + 70, 10))
    # keep sparkles mostly off the text column
    sp = particles(img.size, 70, 7, rmax=9)
    a = np.asarray(sp.getchannel("A"), np.float32)
    a[:, :840] *= 0.25
    sp.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    img.alpha_composite(sp)

    x = 96
    y = section_title(img, 96, "PROFILE  //  01", "ABOUT ME", "自己紹介", x=x, align="l", jp_on_label=True)
    end = draw_rich(img, x, y + 26, [
        ("Hey there you", False, LACE), ("amazing person", True, ICE), ("reading this!", False, LACE),
        ("My name is Marko, I'm a", False, LACE), ("software engineer", True, ICE),
        ("by craft and completely in love with anime. My dream is to visit", False, LACE),
        ("Japan", True, MAGENTA), ("and buy all sorts of anime merch.", False, LACE),
    ], 40, 760, 58)

    y = section_title(img, end + 44, "PROFILE  //  02", "FAVORITE KANJI", "好きな漢字", x=x, align="l",
                      jp_on_label=True)
    # kanji seal
    sx, sy, ss = x, y + 30, 230
    seal = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seal)
    sd.rounded_rectangle((0, 0, ss - 1, ss - 1), 30, fill=rgba(SATIN, 230))
    img.alpha_composite(blur_glow(card_frame((ss + 40, ss + 40), 34, 5, ICE_VIOLET, BLUE, 20), 1),
                        (sx - 20, sy - 20))
    img.alpha_composite(seal, (sx, sy))
    img.alpha_composite(card_frame((ss + 40, ss + 40), 34, 5, ICE_VIOLET, BLUE, 20), (sx - 20, sy - 20))
    draw_text(img, (sx + ss // 2, sy + ss // 2 - 14), "愛", font("serifjp", 150, "Black"),
              anchor="mm", gradient_stops=ICE_VIOLET, glow=BLUE, glow_radius=18)
    draw_text(img, (sx + ss // 2, sy + ss - 28), "あい", font("sansjp", 26, "Medium"), fill=SILVER,
              anchor="mm", tracking=6, shadow=False)
    ImageDraw.Draw(img)
    rd = ImageDraw.Draw(img)
    ribbon_x(rd, sx + ss - 4, sy + 4, 12, MAGENTA, 6)
    draw_rich(img, sx + ss + 50, sy + 6, [
        ("My favorite kanji is", False, LACE), ("愛.", True, ICE), ("It's read as", False, LACE),
        ("\"ai\"", True, ICE), ("meaning", False, LACE), ("\"Love\".", True, MAGENTA),
        ("I like it because love drives us and the kanji itself is so amazing looking!", False, LACE),
    ], 36, 410, 52)
    save(finish_card(img), "intro.webp")


# ---------------------------------------------------------------- stats

def stats():
    H = 830
    img = panel_base(H, focus=(0.7, 0.4))
    img.alpha_composite(particles(img.size, 50, 11, rmax=8))
    y = section_title(img, 70, "ANILIST ARCHIVE", "STATISTICS", "統計")

    panels = [
        (80, BLUE, (ICE, BLUE), "ANIME", "457", [("9,607", "EPISODES"), ("158.9", "DAYS WATCHED")],
         84.7, "Action · Fantasy · Adventure"),
        (744, VIOLET, (LILAC, VIOLET), "MANGA", "359", [("23,094", "CHAPTERS"), ("64", "CHAPTERS / TITLE")],
         93.8, "Action · Fantasy · Adventure"),
    ]
    for px, tint, stops, kind, big, rows, score, genres in panels:
        top, w, h = y + 30, 616, 520
        glass(img, (px, top, px + w, top + h), tint)
        draw_text(img, (px + 44, top + 64), kind, font("bahn", 38, "SemiBold"), fill=stops[0],
                  anchor="ls", tracking=10, shadow=False)
        draw_text(img, (px + 40, top + 200), big, font("bahn", 150, "Bold Condensed"), anchor="ls",
                  gradient_stops=[(0, stops[0]), (1, stops[1])], glow=tint, glow_radius=20)
        draw_text(img, (px + 44, top + 244), "TITLES TRACKED", font("bahn", 28, "SemiBold"),
                  fill=SILVER, anchor="ls", tracking=5, shadow=False)
        for i, (num, lab) in enumerate(rows):
            ry = top + 336 + i * 74
            d = ImageDraw.Draw(img)
            diamond(d, px + 52, ry - 14, 7, fill=rgba(stops[0]))
            draw_text(img, (px + 74, ry), num, font("bahn", 54, "Bold"), fill=LACE, anchor="ls")
            draw_text(img, (px + 74 + font("bahn", 54, "Bold").getlength(num) + 16, ry - 4), lab,
                      font("bahn", 28, "SemiBold"), fill=SILVER, anchor="ls", tracking=4, shadow=False)
        arc_gauge(img, (px + w - 136, top + 146), 84, score, stops, label="MEAN SCORE")
        diamond(ImageDraw.Draw(img), px + 52, top + h - 46, 8, fill=rgba(stops[0]))
        draw_text(img, (px + 70, top + h - 36), genres.upper(),
                  font("bahn", 28, "SemiBold"), fill=stops[0], anchor="ls", tracking=3, shadow=False)
    # morning-star chain between the two panels
    d = ImageDraw.Draw(img)
    cx = 720
    for i, yy in enumerate(range(y + 60, y + 480, 22)):
        if i % 2:  # side-on link
            d.rounded_rectangle((cx - 2, yy - 13, cx + 2, yy + 13), 2, fill=rgba(SILVER, 190))
        else:      # face-on link
            d.rounded_rectangle((cx - 8, yy - 14, cx + 8, yy + 14), 8, outline=rgba(SILVER, 170), width=3)
    sparkle(d, cx, y + 265, 22, ICE)
    draw_text(img, (W // 2, H - 30), "snapshot  ·  November 2026",
              font("segoe", 26), fill=(120, 130, 170), anchor="ms", shadow=False)
    save(finish_card(img), "stats.webp")


# ---------------------------------------------------------------- top 3

def top3():
    H = 1230
    img = panel_base(H, focus=(0.5, 0.8))
    rz = cover(Image.open(COVERS / "rezero_banner.jpg").convert("RGBA"), (W, H), (0.5, 0.5))
    img.alpha_composite(Image.blend(Image.new("RGBA", rz.size, (0, 0, 0, 0)),
                                    rz.filter(ImageFilter.GaussianBlur(14)), 0.18))
    img.alpha_composite(particles(img.size, 80, 3, rmax=10))
    y = section_title(img, 70, "MY ALL-TIME", "TOP 3 ANIME", "三選")

    entries = [  # rank, file, title, jp, size, x, stops, glow
        (2, "shield.jpg", "SHIELD HERO", "盾の勇者の成り上がり", (370, 530), 86, ICE_VIOLET, BLUE),
        (3, "geass.jpg", "CODE GEASS", "コードギアス", (370, 530), 984, [(0, LILAC), (1, VIOLET)], VIOLET),
        (1, "rezero.jpg", "RE:ZERO", "Re:ゼロから始める異世界生活", (450, 650), 495, [(0, ICE), (0.5, MAGENTA), (1, VIOLET)], MAGENTA),
    ]
    base_y = y + 130
    bottom = base_y + 650
    for rank, f, title, jp, (w, h), x, stops, glow in entries:
        card, pad = framed_cover(COVERS / f, (w, h), stops, glow, focus=(0.5, 0.25))
        top = bottom - h
        img.alpha_composite(card, (x - pad, top - pad))
        # big rank numeral overlapping the lower-left corner
        draw_text(img, (x - 18, bottom + 34), f"#{rank}", font("bahn", 190 if rank == 1 else 150, "Bold Condensed"),
                  anchor="ls", gradient_stops=[(0, stops[0][1]), (1, stops[-1][1])], glow=glow,
                  glow_radius=22, glow_strength=1.3)
        # title plate
        ty = bottom + 70
        plate_w = w
        plate = gradient(plate_w, 70, [(0, rgba(stops[0][1], 230)), (1, rgba(stops[-1][1], 230))])
        plate.putalpha(Image.fromarray(np.minimum(np.asarray(plate.getchannel("A")),
                                                  np.asarray(rounded_mask((plate_w, 70), 14))), "L"))
        img.alpha_composite(plate, (x, ty))
        draw_text(img, (x + plate_w // 2, ty + 52), title, font("bahn", 48, "Bold"), fill=LACE,
                  anchor="ms", tracking=5)
        draw_text(img, (x + plate_w // 2, ty + 114), jp, font("sansjp", 32, "Medium"), fill=SILVER,
                  anchor="ms", shadow=False)
        if rank == 1:  # crown
            d = ImageDraw.Draw(img)
            cx, cy = x + w // 2, top - 46
            crown = [(cx - 62, cy + 30), (cx - 70, cy - 22), (cx - 32, cy + 4), (cx, cy - 40),
                     (cx + 32, cy + 4), (cx + 70, cy - 22), (cx + 62, cy + 30)]
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(crown, fill=rgba(GOLD))
            img.alpha_composite(blur_glow(layer, 14, 1.4))
            g = gradient(W, H, [(0, GOLD), (1, (255, 240, 190))], "v")
            g.putalpha(layer.getchannel("A"))
            img.alpha_composite(g)
            for px_ in (-70, 0, 70):
                d.ellipse((cx + px_ - 8, cy - (40 if px_ == 0 else 22) - 8, cx + px_ + 8,
                           cy - (40 if px_ == 0 else 22) + 8), fill=rgba(MAGENTA if px_ == 0 else ICE))
    save(finish_card(img), "top3.webp")


# ---------------------------------------------------------------- firsts & favourites

def firsts():
    H = 900
    img = panel_base(H, focus=(0.3, 0.2))
    img.alpha_composite(particles(img.size, 50, 5, rmax=8))
    y = section_title(img, 70, "ORIGIN POINTS", "FIRSTS & FAVORITES", "原点")
    items = [
        ("fmab.jpg", "#1", "FIRST ANIME", "FMA: Brotherhood", BLUE),
        ("redo.jpg", "#1", "FIRST MANGA", "Redo of Healer", VIOLET),
        ("rezero.jpg", "FAV", "FAVORITE ANIME", "Re:Zero", MAGENTA),
        ("solo.jpg", "FAV", "FAVORITE MANGA", "Solo Leveling", ICE),
    ]
    w, h, gap = 290, 420, 44
    x0 = (W - (4 * w + 3 * gap)) // 2
    top = y + 50
    for i, (f, mark, label, title, col) in enumerate(items):
        x = x0 + i * (w + gap)
        stops = [(0, col), (1, VIOLET if col != VIOLET else BLUE)]
        card, pad = framed_cover(COVERS / f, (w, h), stops, col, radius=22, focus=(0.5, 0.2))
        img.alpha_composite(card, (x - pad, top - pad))
        draw_text(img, (x - 10, top + h + 30), mark, font("bahn", 120, "Bold Condensed"), anchor="ls",
                  gradient_stops=[(0, col), (1, VIOLET)], glow=col, glow_radius=16)
        draw_text(img, (x + 4, top + h + 80), label, font("bahn", 29, "SemiBold"), fill=col,
                  anchor="ls", tracking=2, shadow=False)
        draw_text(img, (x + 4, top + h + 132), title, font("bahn", 44, "Bold Condensed"), fill=LACE, anchor="ls")
    save(finish_card(img), "firsts.webp")


# ---------------------------------------------------------------- section headers

def header(name, label, title, jp, ornament="lace", seed=1):
    H = 330
    img = panel_base(H, focus=(0.5, (seed % 5) / 5))
    img.alpha_composite(particles(img.size, 34, seed, rmax=8))
    section_title(img, 60, label, title, jp, rule=False)
    orn = Image.open(ART / f"orn-{ornament}.png").convert("RGBA")
    bw = W - 120
    band = orn.crop((0, 430, orn.width, 590)).resize((bw, round(160 * bw / orn.width)), Image.LANCZOS)
    screen(img, band, 1.0, (60, H - band.height - 14))
    save(finish_card(img), name)


# ---------------------------------------------------------------- separators

def separator_lace():
    orn = Image.open(ART / "orn-lace.png").convert("RGB")
    band = orn.crop((0, 450, orn.width, 562)).resize((W, round(112 * W / orn.width)), Image.LANCZOS)
    # black -> transparent: alpha from luminance, colour un-premultiplied
    save(black_to_alpha(np.asarray(band, np.float32)), "sep-lace.webp", quality=90)


def separator_sigil():
    H = 90
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cy = H // 2
    line = gradient(W - 200, 3, [(0, rgba(BLUE, 0)), (0.35, rgba(ICE, 230)), (0.5, rgba(ICE, 0)),
                                 (0.65, rgba(VIOLET, 230)), (1, rgba(VIOLET, 0))])
    glow = blur_glow(line, 4, 1.5)
    img.alpha_composite(glow, (100, cy - 1))
    img.alpha_composite(line, (100, cy - 1))
    d = ImageDraw.Draw(img)
    for dx in (-300, -200, 200, 300):
        diamond(d, W // 2 + dx, cy, 7, fill=rgba(ICE if dx < 0 else LILAC))
    diamond(d, W // 2, cy, 34, fill=rgba(VOID, 255), outline=rgba(ICE), width=3)
    draw_text(img, (W // 2, cy + 2), "愛", font("serifjp", 34, "Black"), anchor="mm",
              gradient_stops=ICE_VIOLET, glow=BLUE, glow_radius=8, shadow=False)
    save(img, "sep-sigil.webp", quality=92)


# ---------------------------------------------------------------- socials

def social_plate(name, glyph, label, sub, col):
    w, h, m = 580, 170, 14  # m: margin so the outer glow is not clipped into a hard box
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    body = gradient(w - 2 * m, h - 2 * m, [(0, rgba(INDIGO, 240)), (1, rgba(VOID, 250))], "d")
    body.putalpha(rounded_mask(body.size, 30))
    img.alpha_composite(body, (m, m))
    img.alpha_composite(card_frame((w, h), 28, 3, [(0, col), (1, VIOLET)], col, inset=m))
    d = ImageDraw.Draw(img)
    # hexagon badge with icon glyph
    cx, cy, r = 100, h // 2, 46
    hexa = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(30, 390, 60)]
    d.polygon(hexa, fill=rgba(col, 60), outline=rgba(col), width=3)
    draw_text(img, (cx, cy + 2), glyph, font("icons", 40), fill=LACE, anchor="mm", shadow=False)
    draw_text(img, (180, 86), label, font("bahn", 46, "Bold"), fill=LACE, anchor="ls", tracking=6)
    draw_text(img, (182, 122), sub, font("bahn", 27, "SemiBold"), fill=col, anchor="ls", tracking=4,
              shadow=False)
    draw_text(img, (w - 60, cy + 4), "", font("icons", 30), fill=col, anchor="mm", shadow=False)
    save(img, name, quality=92)


def footer():
    H = 420
    img = panel_base(H, focus=(0.5, 0.9))
    rem = Image.open(ART / "waifu-rem.png").convert("RGBA")
    ring = Image.new("RGBA", (340, 340), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((6, 6, 333, 333), outline=rgba(ICE), width=6)
    m = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 299, 299), fill=255)
    face = cover(rem, (300, 300), (0.5, 0.18))
    face.putalpha(m)
    cx = W - 300
    img.alpha_composite(blur_glow(ring, 14, 2.0), (cx - 170, 40))
    img.alpha_composite(face, (cx - 150, 60))
    img.alpha_composite(ring, (cx - 170, 40))
    img.alpha_composite(particles(img.size, 40, 21, rmax=9))
    draw_text(img, (110, 150), "THANKS FOR", font("bahn", 64, "Bold"), anchor="ls", tracking=6,
              fill=LACE)
    draw_text(img, (110, 250), "STOPPING BY", font("bahn", 104, "Bold"), anchor="ls", tracking=6,
              gradient_stops=ICE_VIOLET, glow=BLUE, glow_radius=18)
    draw_text(img, (114, 312), "ありがとう  ·  またね", font("serifjp", 40, "Bold"), fill=LILAC,
              anchor="ls", glow=VIOLET, glow_radius=10)
    draw_text(img, (114, 362), "Rem approves of your taste in profiles.", font("segoe", 36), fill=SILVER,
              anchor="ls")
    d = ImageDraw.Draw(img)
    ribbon_x(d, cx + 104, 92, 16, MAGENTA, 8)
    save(finish_card(img), "footer.webp")


if __name__ == "__main__":
    intro()
    stats()
    top3()
    firsts()
    header("head-waifu.webp", "CHARACTER FILES", "WAIFU COLLECTION", "俺の嫁", "morningstar", 2)
    header("head-music.webp", "ON REPEAT", "NOW PLAYING", "♪ お気に入り", "lace", 4)
    header("head-milestones.webp", "ACHIEVEMENTS", "EPISODE MILESTONES", "視聴記録", "lace", 6)
    header("head-genres.webp", "ACHIEVEMENTS", "GENRE MASTERY", "ジャンル", "morningstar", 8)
    header("head-socials.webp", "FIND ME", "BEYOND THE ARCHIVE", "リンク", "lace", 9)
    separator_lace()
    separator_sigil()
    social_plate("social-steam.webp", "", "STEAM", "LET'S PLAY TOGETHER", BLUE)
    social_plate("social-youtube.webp", "", "YOUTUBE", "WATCH MY CHANNEL", MAGENTA)
    footer()
