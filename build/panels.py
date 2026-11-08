"""Static profile panels (WebP, 1440 px wide).

AniList shows the About column ~514 css px wide (measured), so text is sized to stay
readable at ~0.36x. Sections deliberately vary in shape, alignment and colour so the
page doesn't read as one long stack of identical boxes.

Run: python build/panels.py   (needs build/covers from build/fetch_covers.py)
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from common import (ART, BLUE, CORAL, COVERS, GOLD, GOLD_CORAL, ICE, ICE_PINK, ICE_VIOLET, INDIGO,
                    LACE, LILAC, MAGENTA, MINT, MINT_BLUE, MINT_PINK, RAINBOW, SATIN, SILVER, VIOLET,
                    VOID, W, black_to_alpha, blur_glow, card_frame, cover, diamond, draw_rich,
                    draw_text, finish_card, font, glass, gradient, mix, panel_base, particles, rgba,
                    ribbon_x, rotated, rounded_mask, save, screen, section_title, sparkle)


# ---------------------------------------------------------------- shared pieces

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
    for i in range(int(360 * value / 100)):
        sd.arc((x - r, y - r, x + r, y + r), -90 + i, -88 + i, fill=rgba(mix(stops[0], stops[1], i / 360)),
               width=width)
    img.alpha_composite(blur_glow(seg, 8, 1.3))
    img.alpha_composite(seg)
    draw_text(img, (x, y + 6), f"{value:.1f}", font("bahn", 52, "Bold Condensed"), anchor="mm",
              fill=LACE, shadow=False)
    if label:
        draw_text(img, (x, y + r + 34), label, font("bahn", 28, "SemiBold"), fill=SILVER,
                  anchor="mm", tracking=4, shadow=False)


def soft_glow_spot(img, box, col, alpha, blur):
    spot = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(spot).ellipse(box, fill=rgba(col, alpha))
    img.alpha_composite(spot.filter(ImageFilter.GaussianBlur(blur)))


# ---------------------------------------------------------------- intro

def intro():
    H = 1180
    img = panel_base(H, focus=(0.2, 0.5))
    soft_glow_spot(img, (-200, 700, 500, 1300), MAGENTA, 70, 120)
    rem = Image.open(ART / "intro-rem.png").convert("RGBA")
    rh = 1280
    rem = rem.resize((round(rem.width * rh / rem.height), rh), Image.LANCZOS)
    m = np.ones((rem.height, rem.width), np.float32)
    fx = np.clip(np.linspace(0, 1, rem.width) / 0.12, 0, 1)
    fy = np.clip((np.linspace(1, 0, rem.height)) / 0.25, 0, 1)
    ft = np.clip(np.linspace(0, 1, rem.height) / 0.06, 0, 1)
    m *= fx[None, :] * fy[:, None] * ft[:, None]
    rem.putalpha(Image.fromarray((m * 255).astype(np.uint8), "L"))
    soft_glow_spot(img, (900, 80, 1420, 600), VIOLET, 90, 90)
    soft_glow_spot(img, (1000, 500, 1500, 1000), MINT, 50, 110)
    img.alpha_composite(rem, (W - rem.width + 70, 10))
    sp = particles(img.size, 70, 7, rmax=9, colours=(ICE, MAGENTA, LACE, MINT))
    a = np.asarray(sp.getchannel("A"), np.float32)
    a[:, :840] *= 0.25  # keep sparkles mostly off the text column
    sp.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    img.alpha_composite(sp)

    x = 96
    y = section_title(img, 96, "PROFILE  //  01", "ABOUT ME", "自己紹介", x=x, align="l", jp_on_label=True,
                      stops=ICE_PINK)
    end = draw_rich(img, x, y + 26, [
        ("Hey there you", False, LACE), ("amazing person", True, ICE), ("reading this!", False, LACE),
        ("My name is Marko, I'm a", False, LACE), ("software engineer", True, MINT),
        ("by craft and completely in love with anime. My dream is to visit", False, LACE),
        ("Japan", True, MAGENTA), ("and buy all sorts of anime merch.", False, LACE),
    ], 40, 760, 58)

    y = section_title(img, end + 44, "PROFILE  //  02", "FAVORITE KANJI", "好きな漢字", x=x, align="l",
                      jp_on_label=True, stops=MINT_PINK, glow=VIOLET, label_col=MINT)
    sx, sy, ss = x, y + 30, 230
    seal = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    ImageDraw.Draw(seal).rounded_rectangle((0, 0, ss - 1, ss - 1), 30, fill=rgba(SATIN, 230))
    frame = card_frame((ss + 40, ss + 40), 34, 5, MINT_PINK, MAGENTA, 20)
    img.alpha_composite(seal, (sx, sy))
    img.alpha_composite(frame, (sx - 20, sy - 20))
    draw_text(img, (sx + ss // 2, sy + ss // 2 - 14), "愛", font("serifjp", 150, "Black"),
              anchor="mm", gradient_stops=ICE_PINK, glow=MAGENTA, glow_radius=18)
    draw_text(img, (sx + ss // 2, sy + ss - 28), "あい", font("sansjp", 26, "Medium"), fill=SILVER,
              anchor="mm", tracking=6, shadow=False)
    ribbon_x(ImageDraw.Draw(img), sx + ss - 4, sy + 4, 12, MAGENTA, 6)
    draw_rich(img, sx + ss + 50, sy + 6, [
        ("My favorite kanji is", False, LACE), ("愛.", True, MAGENTA), ("It's read as", False, LACE),
        ("\"ai\"", True, ICE), ("meaning", False, LACE), ("\"Love\".", True, MAGENTA),
        ("I like it because love drives us and the kanji itself is so amazing looking!", False, LACE),
    ], 36, 410, 52)
    save(finish_card(img, stops=ICE_PINK), "intro.webp")


# ---------------------------------------------------------------- stats ("tech" chamfered card)

def stats():
    H = 830
    img = panel_base(H, bg="aurora", focus=(0.5, 0.5), dim=0.7)
    img.alpha_composite(particles(img.size, 50, 11, rmax=8, colours=(MINT, MAGENTA, LACE, ICE)))
    y = section_title(img, 70, "ANILIST ARCHIVE", "STATISTICS", "統計", stops=MINT_PINK, glow=MINT,
                      label_col=MINT)
    panels = [
        (80, MINT, (MINT, BLUE), "ANIME", "457", [("9,607", "EPISODES"), ("158.9", "DAYS WATCHED")],
         84.7, "Action · Fantasy · Adventure"),
        (744, MAGENTA, (MAGENTA, VIOLET), "MANGA", "359", [("23,094", "CHAPTERS"), ("64", "CHAPTERS / TITLE")],
         93.8, "Action · Fantasy · Adventure"),
    ]
    for px, tint, stops, kind, big, rows, score, genres in panels:
        top, w, h = y + 30, 616, 520
        glass(img, (px, top, px + w, top + h), tint, radius=34, shape="chamfer")
        draw_text(img, (px + 44, top + 64), kind, font("bahn", 38, "SemiBold"), fill=stops[0],
                  anchor="ls", tracking=10, shadow=False)
        draw_text(img, (px + 40, top + 200), big, font("bahn", 150, "Bold Condensed"), anchor="ls",
                  gradient_stops=[(0, stops[0]), (1, stops[1])], glow=tint, glow_radius=20)
        draw_text(img, (px + 44, top + 244), "TITLES TRACKED", font("bahn", 28, "SemiBold"),
                  fill=SILVER, anchor="ls", tracking=5, shadow=False)
        d = ImageDraw.Draw(img)
        for i, (num, lab) in enumerate(rows):
            ry = top + 336 + i * 74
            diamond(d, px + 52, ry - 14, 7, fill=rgba(stops[0]))
            draw_text(img, (px + 74, ry), num, font("bahn", 54, "Bold"), fill=LACE, anchor="ls")
            draw_text(img, (px + 74 + font("bahn", 54, "Bold").getlength(num) + 16, ry - 4), lab,
                      font("bahn", 28, "SemiBold"), fill=SILVER, anchor="ls", tracking=4, shadow=False)
        arc_gauge(img, (px + w - 136, top + 146), 84, score, stops, label="MEAN SCORE")
        diamond(d, px + 52, top + h - 46, 8, fill=rgba(stops[0]))
        draw_text(img, (px + 70, top + h - 36), genres.upper(), font("bahn", 28, "SemiBold"), fill=stops[0],
                  anchor="ls", tracking=3, shadow=False)
    d = ImageDraw.Draw(img)
    cx = 720
    for i, yy in enumerate(range(y + 60, y + 480, 22)):
        if i % 2:
            d.rounded_rectangle((cx - 2, yy - 13, cx + 2, yy + 13), 2, fill=rgba(SILVER, 190))
        else:
            d.rounded_rectangle((cx - 8, yy - 14, cx + 8, yy + 14), 8, outline=rgba(SILVER, 170), width=3)
    sparkle(d, cx, y + 265, 22, LACE)
    draw_text(img, (W // 2, H - 30), "snapshot  ·  November 2026", font("segoe", 26), fill=(150, 160, 190),
              anchor="ms", shadow=False)
    save(finish_card(img, radius=30, stops=MINT_PINK, shape="chamfer", glow_col=MINT), "stats.webp")


# ---------------------------------------------------------------- top 3

def top3():
    H = 1230
    img = panel_base(H, bg="aurora", focus=(0.5, 0.15), dim=0.75)
    rz = cover(Image.open(COVERS / "rezero_banner.jpg").convert("RGBA"), (W, H), (0.5, 0.5))
    img.alpha_composite(Image.blend(Image.new("RGBA", rz.size, (0, 0, 0, 0)),
                                    rz.filter(ImageFilter.GaussianBlur(14)), 0.15))
    img.alpha_composite(particles(img.size, 80, 3, rmax=10, colours=(GOLD, MAGENTA, ICE, LACE)))
    y = section_title(img, 70, "MY ALL-TIME", "TOP 3 ANIME", "三選",
                      stops=[(0, GOLD), (0.5, MAGENTA), (1, VIOLET)], glow=MAGENTA, label_col=GOLD)
    entries = [  # rank, file, title, jp, size, x, stops, glow
        (2, "shield.jpg", "SHIELD HERO", "盾の勇者の成り上がり", (370, 530), 86, [(0, MINT), (1, BLUE)], MINT),
        (3, "geass.jpg", "CODE GEASS", "コードギアス", (370, 530), 984, [(0, LILAC), (1, VIOLET)], VIOLET),
        (1, "rezero.jpg", "RE:ZERO", "Re:ゼロから始める異世界生活", (450, 650), 495,
         [(0, GOLD), (0.5, MAGENTA), (1, VIOLET)], MAGENTA),
    ]
    bottom = y + 130 + 650
    for rank, f, title, jp, (w, h), x, stops, glow in entries:
        card, pad = framed_cover(COVERS / f, (w, h), stops, glow, focus=(0.5, 0.25))
        top = bottom - h
        img.alpha_composite(card, (x - pad, top - pad))
        draw_text(img, (x - 18, bottom + 34), f"#{rank}", font("bahn", 190 if rank == 1 else 150, "Bold Condensed"),
                  anchor="ls", gradient_stops=[(0, stops[0][1]), (1, stops[-1][1])], glow=glow,
                  glow_radius=22, glow_strength=1.3)
        ty = bottom + 70
        plate = gradient(w, 70, [(0, rgba(stops[0][1], 230)), (1, rgba(stops[-1][1], 230))])
        plate.putalpha(Image.fromarray(np.minimum(np.asarray(plate.getchannel("A")),
                                                  np.asarray(rounded_mask((w, 70), 14))), "L"))
        img.alpha_composite(plate, (x, ty))
        draw_text(img, (x + w // 2, ty + 52), title, font("bahn", 48, "Bold"), fill=LACE, anchor="ms", tracking=5)
        draw_text(img, (x + w // 2, ty + 114), jp, font("sansjp", 32, "Medium"), fill=SILVER, anchor="ms",
                  shadow=False)
        if rank == 1:  # crown
            cx, cy = x + w // 2, top - 46
            crown = [(cx - 62, cy + 30), (cx - 70, cy - 22), (cx - 32, cy + 4), (cx, cy - 40),
                     (cx + 32, cy + 4), (cx + 70, cy - 22), (cx + 62, cy + 30)]
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(crown, fill=rgba(GOLD))
            img.alpha_composite(blur_glow(layer, 14, 1.4))
            g = gradient(W, H, [(0, GOLD), (1, (255, 240, 190))], "v")
            g.putalpha(layer.getchannel("A"))
            img.alpha_composite(g)
            d = ImageDraw.Draw(img)
            for px_ in (-70, 0, 70):
                py_ = cy - (40 if px_ == 0 else 22)
                d.ellipse((cx + px_ - 8, py_ - 8, cx + px_ + 8, py_ + 8), fill=rgba(MAGENTA if px_ == 0 else ICE))
    save(finish_card(img, stops=[(0, GOLD), (0.5, MAGENTA), (1, VIOLET)], glow_col=MAGENTA), "top3.webp")


# ---------------------------------------------------------------- firsts & favourites (scattered polaroids)

def polaroid(src, mark, label, title, col, angle):
    pw, ph = 268, 380
    m_side, m_bottom = 16, 112
    w, h = pw + 2 * m_side, ph + m_side + m_bottom
    card = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    ox, oy = 30, 30
    paper = Image.new("RGBA", (w, h), rgba((246, 244, 252)))
    paper.putalpha(rounded_mask((w, h), 10))
    card.alpha_composite(paper, (ox, oy))
    photo = cover(Image.open(src).convert("RGBA"), (pw, ph), (0.5, 0.2))
    photo.putalpha(rounded_mask((pw, ph), 6))
    card.alpha_composite(photo, (ox + m_side, oy + m_side))
    d = ImageDraw.Draw(card)
    draw_text(card, (ox + m_side + 2, oy + m_side + ph + 42), label, font("bahn", 27, "Bold"), fill=col,
              anchor="ls", tracking=2, shadow=False)
    draw_text(card, (ox + m_side + 2, oy + m_side + ph + 90), title, font("bahn", 42, "Bold Condensed"),
              fill=SATIN, anchor="ls", shadow=False)
    # round sticker on the photo's top-right corner
    sx, sy, r = ox + w - 40, oy + 40, 50
    st = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(st).ellipse((sx - r, sy - r, sx + r, sy + r), fill=rgba(col))
    card.alpha_composite(blur_glow(st, 10, 1.5))
    g = gradient(card.width, card.height, [(0, mix(col, LACE, 0.25)), (1, col)], "d")
    g.putalpha(st.getchannel("A"))
    card.alpha_composite(g)
    d.ellipse((sx - r + 6, sy - r + 6, sx + r - 6, sy + r - 6), outline=rgba(LACE, 200), width=3)
    draw_text(card, (sx, sy + 2), mark, font("bahn", 46 if len(mark) < 3 else 38, "Bold Condensed"),
              fill=LACE, anchor="mm", shadow=False)
    # washi tape across the top edge
    tape = Image.new("RGBA", (150, 44), rgba(mix(col, LACE, 0.45), 175))
    td = ImageDraw.Draw(tape)
    for i in range(0, 150, 18):
        td.line((i, 0, i + 10, 44), fill=rgba(LACE, 60), width=5)
    tape = rotated(tape, -8 if angle > 0 else 8)
    card.alpha_composite(tape, (ox + w // 2 - tape.width // 2, oy - 22))
    # soft drop shadow, then tilt
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 170))
    sh.putalpha(rounded_mask((w, h), 10).point(lambda v: v * 160 // 255))
    shadow.alpha_composite(sh, (ox + 8, oy + 14))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    shadow.alpha_composite(card)
    return rotated(shadow, angle)


def firsts():
    H = 980
    img = panel_base(H, bg="aurora", focus=(0.1, 0.9), dim=0.8)
    img.alpha_composite(particles(img.size, 50, 5, rmax=8, colours=(MINT, MAGENTA, GOLD, LACE)))
    y = section_title(img, 70, "ORIGIN POINTS", "FIRSTS & FAVORITES", "原点", stops=MINT_PINK, glow=VIOLET,
                      label_col=MINT)
    items = [  # file, sticker, label, title, colour, tilt, x centre, y centre offset
        ("fmab.jpg", "#1", "FIRST ANIME", "FMA: Brotherhood", BLUE, 6, 200, 0),
        ("redo.jpg", "#1", "FIRST MANGA", "Redo of Healer", VIOLET, -4, 540, 60),
        ("rezero.jpg", "FAV", "FAVORITE ANIME", "Re:Zero", MAGENTA, 3, 890, 10),
        ("solo.jpg", "FAV", "FAVORITE MANGA", "Solo Leveling", MINT, -7, 1235, 70),
    ]
    base_cy = y + 330
    for f, mark, label, title, col, angle, cx, dy in items:
        p = polaroid(COVERS / f, mark, label, title, col, angle)
        img.alpha_composite(p, (cx - p.width // 2, base_cy + dy - p.height // 2))
    save(finish_card(img, stops=MINT_PINK, glow_col=VIOLET), "firsts.webp")


# ---------------------------------------------------------------- genre mastery (honeycomb)

GENRES = [  # name, anime count, colour, emblem file; counts from the AniList API (Nov 2026)
    ("FANTASY", 287, VIOLET, "fantasy"),
    ("ACTION", 292, CORAL, "action"),
    ("ADVENTURE", 207, MINT, "adventure"),
    ("COMEDY", 204, GOLD, "comedy"),
    ("DRAMA", 152, MAGENTA, "drama"),
]


def rank_for(count):
    return "MASTER" if count >= 250 else "EXPERT" if count >= 200 else "ADEPT"


def hex_points(cx, cy, r):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 270, 60)]


def genre_hex(img, cx, cy, r, name, count, col, emblem):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(hex_points(cx, cy, r), fill=255)
    fill = gradient(w, h, [(0, rgba(mix(col, VOID, 0.55), 235)), (1, rgba(VOID, 245))], "v")
    fill.putalpha(mask)
    ring = Image.new("L", (w, h), 0)
    ImageDraw.Draw(ring).polygon(hex_points(cx, cy, r - 2), outline=255, width=6)
    gl = Image.new("RGBA", (w, h), rgba(col))
    gl.putalpha(ring)
    img.alpha_composite(blur_glow(gl, 18, 2.0))
    img.alpha_composite(fill)
    art = Image.open(ART / f"genre-{emblem}.png").convert("RGB").resize((210, 210), Image.LANCZOS)
    img.alpha_composite(black_to_alpha(np.asarray(art, np.float32), floor=12), (cx - 105, cy - 196))
    g = gradient(w, h, [(0, mix(col, LACE, 0.5)), (1, col)], "d")
    g.putalpha(ring)
    img.alpha_composite(g)
    draw_text(img, (cx, cy + 58), name, font("bahn", 50, "Bold"), fill=LACE, anchor="ms", tracking=4)
    num_f, lab_f = font("bahn", 60, "Bold Condensed"), font("bahn", 28, "SemiBold")
    num, lab = str(count), "  TITLES"
    total = num_f.getlength(num) + lab_f.getlength(lab)
    x0 = cx - total / 2
    draw_text(img, (x0, cy + 116), num, num_f, fill=col, anchor="ls", glow=col, glow_radius=10)
    draw_text(img, (x0 + num_f.getlength(num), cy + 116), lab, lab_f, fill=SILVER, anchor="ls", shadow=False)
    # rank as tracked text between two diamonds: a chip would poke out of the narrowing hex
    rank = rank_for(count)
    rf = font("bahn", 27, "Bold")
    rw = rf.getlength(rank) + 5 * (len(rank) - 1)
    draw_text(img, (cx, cy + 158), rank, rf, fill=mix(col, LACE, 0.35), anchor="ms", tracking=5, shadow=False)
    d = ImageDraw.Draw(img)
    for sx in (cx - rw / 2 - 22, cx + rw / 2 + 22):
        diamond(d, sx, cy + 148, 7, fill=rgba(col))


def genres():
    H = 1120
    img = panel_base(H, bg="aurora", focus=(0.9, 0.5), dim=0.7)
    img.alpha_composite(particles(img.size, 60, 17, rmax=8, colours=(CORAL, GOLD, MINT, VIOLET, MAGENTA)))
    y = section_title(img, 70, "ACHIEVEMENTS", "GENRE MASTERY", "ジャンル", stops=RAINBOW, glow=VIOLET,
                      label_col=GOLD)
    r = 212
    hw = math.sqrt(3) * r
    gap = 34
    top_cy = y + 36 + r
    row2_cy = top_cy + int(1.5 * r) + gap
    spots = [(720 - hw - gap, top_cy), (720, top_cy), (720 + hw + gap, top_cy),
             (720 - hw / 2 - gap / 2, row2_cy), (720 + hw / 2 + gap / 2, row2_cy)]
    for (cx, cy), (name, count, col, emblem) in zip(spots, GENRES):
        genre_hex(img, int(cx), int(cy), r, name, count, col, emblem)
    draw_text(img, (W // 2, H - 34), "top 5 anime genres by titles watched  ·  November 2026", font("segoe", 26),
              fill=(150, 160, 190), anchor="ms", shadow=False)
    save(finish_card(img, stops=RAINBOW, glow_col=VIOLET), "genres.webp")


# ---------------------------------------------------------------- separators

def separator_lace():
    orn = Image.open(ART / "orn-lace.png").convert("RGB")
    band = orn.crop((0, 450, orn.width, 562)).resize((W, round(112 * W / orn.width)), Image.LANCZOS)
    save(black_to_alpha(np.asarray(band, np.float32)), "sep-lace.webp", quality=90)


def separator_sigil():
    H = 90
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cy = H // 2
    line = gradient(W - 200, 3, [(0, rgba(MINT, 0)), (0.35, rgba(ICE, 230)), (0.5, rgba(ICE, 0)),
                                 (0.65, rgba(MAGENTA, 230)), (1, rgba(VIOLET, 0))])
    img.alpha_composite(blur_glow(line, 4, 1.5), (100, cy - 1))
    img.alpha_composite(line, (100, cy - 1))
    d = ImageDraw.Draw(img)
    for dx in (-300, -200, 200, 300):
        diamond(d, W // 2 + dx, cy, 7, fill=rgba(MINT if dx < 0 else MAGENTA))
    diamond(d, W // 2, cy, 34, fill=rgba(VOID, 255), outline=rgba(ICE), width=3)
    draw_text(img, (W // 2, cy + 2), "愛", font("serifjp", 34, "Black"), anchor="mm",
              gradient_stops=ICE_PINK, glow=MAGENTA, glow_radius=8, shadow=False)
    save(img, "sep-sigil.webp", quality=92)


# ---------------------------------------------------------------- socials + footer

def social_plate(name, glyph, label, sub, col):
    w, h, m = 580, 170, 14  # m: margin so the outer glow is not clipped into a hard box
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    body = gradient(w - 2 * m, h - 2 * m, [(0, rgba(mix(col, INDIGO, 0.7), 240)), (1, rgba(VOID, 250))], "d")
    body.putalpha(rounded_mask(body.size, 30))
    img.alpha_composite(body, (m, m))
    img.alpha_composite(card_frame((w, h), 28, 3, [(0, col), (1, VIOLET)], col, inset=m))
    d = ImageDraw.Draw(img)
    cx, cy, r = 100, h // 2, 46
    hexa = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(30, 390, 60)]
    d.polygon(hexa, fill=rgba(col, 70), outline=rgba(col), width=3)
    draw_text(img, (cx, cy + 2), glyph, font("icons", 40), fill=LACE, anchor="mm", shadow=False)
    draw_text(img, (180, 86), label, font("bahn", 46, "Bold"), fill=LACE, anchor="ls", tracking=6)
    draw_text(img, (182, 122), sub, font("bahn", 27, "SemiBold"), fill=col, anchor="ls", tracking=4,
              shadow=False)
    draw_text(img, (w - 60, cy + 4), "", font("icons", 30), fill=col, anchor="mm", shadow=False)
    save(img, name, quality=92)


def footer():
    H = 420
    img = panel_base(H, bg="aurora", focus=(0.5, 0.95), dim=0.75)
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
    img.alpha_composite(particles(img.size, 40, 21, rmax=9, colours=(ICE, MAGENTA, MINT, LACE)))
    draw_text(img, (110, 150), "THANKS FOR", font("bahn", 64, "Bold"), anchor="ls", tracking=6, fill=LACE)
    draw_text(img, (110, 250), "STOPPING BY", font("bahn", 104, "Bold"), anchor="ls", tracking=6,
              gradient_stops=ICE_PINK, glow=MAGENTA, glow_radius=18)
    draw_text(img, (114, 312), "ありがとう  ·  またね", font("serifjp", 40, "Bold"), fill=LILAC,
              anchor="ls", glow=VIOLET, glow_radius=10)
    draw_text(img, (114, 362), "Rem approves of your taste in profiles.", font("segoe", 36), fill=SILVER,
              anchor="ls")
    ribbon_x(ImageDraw.Draw(img), cx + 104, 92, 16, MAGENTA, 8)
    save(finish_card(img, stops=ICE_PINK, glow_col=MAGENTA), "footer.webp")


if __name__ == "__main__":
    intro()
    stats()
    top3()
    firsts()
    genres()
    separator_lace()
    separator_sigil()
    social_plate("social-steam.webp", "", "STEAM", "LET'S PLAY TOGETHER", BLUE)
    social_plate("social-youtube.webp", "", "YOUTUBE", "WATCH MY CHANNEL", CORAL)
    footer()
