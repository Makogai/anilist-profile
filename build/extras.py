"""Profile banner (AniList settings -> banner, 1700x330 JPG; AniList only takes static banners) and
avatars (settings -> avatar).

AniList crops the banner differently per screen (the centre stays visible) and draws the avatar and
username over its lower-left, so the name sits up in the night sky between the moon and Rem, Rem is
right of centre and the lower-left stays calm.
Outputs: banner.jpg, avatar.png, avatar-sunflower.png.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from animated import shine_band
from common import (ART, BLUE, GOLD, ICE, ICE_VIOLET, LACE, MAGENTA, VIOLET, black_to_alpha, blur_glow, cover,
                    diamond, draw_text, font, gradient, rgba, save, sparkle, text_mask)

BW, BH = 1700, 330
SUN = [(0, (255, 240, 160)), (0.5, GOLD), (1, (255, 150, 60))]
WARM = [(255, 214, 110), (255, 240, 170), (255, 180, 80)]
NAME_STOPS = [(0, LACE), (0.35, ICE), (0.7, VIOLET), (1, MAGENTA)]
MOON = (398, 100)


def banner_name(img, cx=660, base=114, max_w=362):
    """MAKOGAI in the sky between moon and Rem: colour-split ghosts, double glow, gradient fill, a light
    streak and sparkles, over a gold rule with the name in katakana."""
    text, tracking = "MAKOGAI", 12
    size = 96
    while True:  # biggest size that still fits between the moon and Rem's hair
        f = font("bahn", size, "Bold")
        m = text_mask(img.size, (cx, base), text, f, "ms", tracking)
        x0, y0, x1, y1 = m.getbbox()
        if x1 - x0 <= max_w:
            break
        size -= 2
    mask = np.asarray(m, np.float32) / 255
    halo = Image.new("RGBA", img.size, rgba(MAGENTA))  # wide magenta halo
    halo.putalpha(m)
    img.alpha_composite(blur_glow(halo, 30, 1.3))
    for col, dx in ((ICE, -5), (MAGENTA, 5)):  # chromatic split
        ghost = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_text(ghost, (cx + dx, base), text, f, fill=col, anchor="ms", tracking=tracking, shadow=False)
        a = np.asarray(ghost.getchannel("A"), np.float32) * 0.6
        ghost.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
        img.alpha_composite(ghost)
    draw_text(img, (cx, base), text, f, anchor="ms", tracking=tracking, gradient_stops=NAME_STOPS, glow=BLUE,
              glow_radius=14, glow_strength=1.2)
    streak = np.asarray(shine_band(img.size, x0 + (x1 - x0) * 0.62, 34, 0.35,
                                   colours=((255, 255, 255), ICE, (255, 255, 255)), strength=230), np.float32)
    streak[..., 3] *= mask
    img.alpha_composite(Image.fromarray(streak.astype(np.uint8), "RGBA"))
    d = ImageDraw.Draw(img)
    sparkle(d, x0 + 6, y0 + 4, 16, LACE)
    sparkle(d, x1 - 4, y0 - 6, 22, LACE)
    sparkle(d, x0 - 20, y1 - 8, 9, GOLD)
    # gold rule with a diamond, then マコガイ
    ry = base + 22
    rule = gradient(x1 - x0 + 40, 3, [(0, rgba(GOLD, 0)), (0.5, rgba(GOLD, 255)), (1, rgba(GOLD, 0))])
    img.alpha_composite(blur_glow(rule, 4, 1.5), (x0 - 20, ry))
    img.alpha_composite(rule, (x0 - 20, ry))
    diamond(d, cx, ry + 1, 7, fill=rgba(GOLD), outline=rgba(LACE), width=1)
    draw_text(img, (cx, ry + 44), "マコガイ", font("serifjp", 30, "Bold"), anchor="ms", tracking=14,
              gradient_stops=SUN, glow=GOLD, glow_radius=10)
    print(f"name: {size}px, x {x0}-{x1}, y {y0}-{y1}")


def banner():
    img = cover(Image.open(ART / "banner-rem-wide.png").convert("RGBA"), (BW, BH), (0.5, 0.49))
    g = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))  # soft moon halo
    ImageDraw.Draw(g).ellipse((MOON[0] - 100, MOON[1] - 100, MOON[0] + 100, MOON[1] + 100), fill=rgba(ICE, 55))
    img.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
    rng = np.random.default_rng(5)
    fx_layer = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    d = ImageDraw.Draw(fx_layer)
    for _ in range(46):  # fireflies over the field
        x, y, s = rng.uniform(0, BW), rng.uniform(80, BH), rng.uniform(2.0, 4.5)
        d.ellipse((x - s, y - s, x + s, y + s), fill=rgba(WARM[rng.integers(0, 3)], int(rng.uniform(140, 255))))
    for _ in range(9):  # tumbling golden petals
        x, y, ang = rng.uniform(0, BW), rng.uniform(0, BH), rng.uniform(0, 2 * math.pi)
        pts = [(x + 11 * math.cos(ang + a) * (1 if j % 2 == 0 else 0.45),
                y + 11 * math.sin(ang + a) * (1 if j % 2 == 0 else 0.45))
               for j, a in enumerate((0, math.pi / 2, math.pi, 3 * math.pi / 2))]
        d.polygon(pts, fill=rgba(GOLD, 220))
    hx, hy = 1185, 44  # shooting star heading down-left, tail ending before 向日葵
    for j in range(26):
        tx, ty = hx + j * 7.2, hy - j * 1.0
        r = 3 - j * 0.1
        d.ellipse((tx - r, ty - r, tx + r, ty + r), fill=rgba(LACE, int(255 * (1 - j / 26))))
    sparkle(d, hx, hy, 13, LACE)
    img.alpha_composite(blur_glow(fx_layer, 6, 1.6))
    img.alpha_composite(fx_layer)
    # 向日葵 in gold, top right: favourite kanji next to the favourite girl
    draw_text(img, (1490, 92), "向日葵", font("serifjp", 66, "Black"), anchor="ms", tracking=10,
              gradient_stops=SUN, glow=GOLD, glow_radius=16)
    draw_text(img, (1490, 128), "ひまわり", font("sansjp", 24, "Medium"), fill=LACE, anchor="ms", tracking=8,
              shadow=False)
    banner_name(img)
    save(img, "banner.jpg", quality=93)


def ring_avatar(face_img, ring_stops, glow_col, name, sticker=None):
    s = 460
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    m = Image.new("L", face_img.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, face_img.width - 1, face_img.height - 1), fill=255)
    face_img.putalpha(m)
    ring_l = Image.new("L", (s, s), 0)
    ImageDraw.Draw(ring_l).ellipse((10, 10, s - 11, s - 11), outline=255, width=12)
    ring = gradient(s, s, ring_stops, "d")
    ring.putalpha(ring_l)
    glow = Image.new("RGBA", (s, s), rgba(glow_col))
    glow.putalpha(ring_l)
    img.alpha_composite(blur_glow(glow, 8, 1.4))
    img.alpha_composite(face_img, (20, 20))
    img.alpha_composite(ring)
    if sticker is not None:
        img.alpha_composite(sticker, (s - sticker.width - 4, s - sticker.height - 4))
    save(img, name)


def avatar():
    face = cover(Image.open(ART / "waifu-rem.png").convert("RGBA"), (420, 420), (0.5, 0.15))
    ring_avatar(face, ICE_VIOLET, ICE, "avatar.png")


def avatar_sunflower():
    """Variant: smiling Rem holding her sunflower, gold-to-blue ring, sunflower badge on the ring."""
    art = Image.open(ART / "banner-rem.png").convert("RGBA")
    face = art.crop((575, 215, 1185, 825)).resize((420, 420), Image.LANCZOS)
    flower = Image.open(ART / "sunflower.png").convert("RGB").resize((130, 130), Image.LANCZOS)
    badge = black_to_alpha(np.asarray(flower, np.float32), floor=12)
    ring_avatar(face, [(0, (255, 240, 160)), (0.45, GOLD), (1, (90, 150, 255))], GOLD, "avatar-sunflower.png",
                sticker=badge)


if __name__ == "__main__":
    banner()
    avatar()
    avatar_sunflower()
