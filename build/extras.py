"""Profile banner (AniList settings -> banner, 1700x330) and avatars (settings -> avatar).

AniList crops the banner differently per screen (centre stays visible) and draws the avatar and
username over its lower-left, so Rem sits right of centre and the lower-left stays calm.
Outputs: banner.gif (animated: wind through the sunflowers, Rem's hair and ribbon, fireflies,
petals, moon glow, a shooting star), banner.jpg (static fallback), avatar.png, avatar-sunflower.png.
"""
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from common import (ART, GOLD, ICE, ICE_VIOLET, LACE, OUT, black_to_alpha, blur_glow, cover, draw_text, font,
                    gradient, rgba, save, sparkle)
from live import Animator, ellipse_mask, hsv_mask, to_np, to_pil

BW, BH = 1700, 330
SUN = [(0, (255, 240, 160)), (0.5, GOLD), (1, (255, 150, 60))]
WARM = [(255, 214, 110), (255, 240, 170), (255, 180, 80)]


def banner_frames(n=48):
    art = to_np(cover(Image.open(ART / "banner-rem-wide.png").convert("RGBA"), (BW, BH), (0.5, 0.49)))
    anim = Animator(art)
    rgb = art[..., :3]
    xx, yy = anim.xx, anim.yy
    rem_zone = np.clip((xx - 830) / 30, 0, 1) * np.clip((1150 - xx) / 30, 0, 1)
    face = ellipse_mask(art.shape, (985, 150), (85, 95), 12)
    hair = hsv_mask(rgb, (195, 235), 0.35, 0.42, 3) * rem_zone * (1 - face)
    ribbon = hsv_mask(rgb, (300, 345), 0.3, 0.35, 3) * np.clip((xx - 1040) / 20, 0, 1)
    flowers = hsv_mask(rgb, (30, 62), 0.45, 0.5, 3) * np.clip((yy - 120) / 40, 0, 1)

    over = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    # 向日葵 in gold, top right: favourite kanji next to the favourite girl
    draw_text(over, (1490, 92), "向日葵", font("serifjp", 66, "Black"), anchor="ms", tracking=10,
              gradient_stops=SUN, glow=GOLD, glow_radius=16)
    draw_text(over, (1490, 128), "ひまわり", font("sansjp", 24, "Medium"), fill=LACE, anchor="ms", tracking=8,
              shadow=False)

    rng = np.random.default_rng(5)
    F = 46  # fireflies
    fx, fy = rng.uniform(0, BW, F), rng.uniform(80, BH, F)
    fph, fsz = rng.uniform(0, 2 * math.pi, F), rng.uniform(2.0, 4.5, F)
    fcol = rng.integers(0, len(WARM), F)
    P = 9  # falling petals
    px, py, pph = rng.uniform(0, BW, P), rng.uniform(0, BH, P), rng.uniform(0, 2 * math.pi, P)
    moon = (398, 52)
    frames = []
    for i in range(n):
        t = i / n
        anim.sway(flowers, 2 * t, 2.6, wavelength=300, vertical=0.6, along=(1.0, 0.15))
        anim.sway(hair, 2 * t, 2.2, wavelength=110)
        anim.sway(ribbon, 3 * t + 0.2, 3.5, wavelength=60)
        f = to_pil(anim.render())
        g = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))  # moon glow breathing
        r = 92 + 12 * math.sin(2 * math.pi * t)
        ImageDraw.Draw(g).ellipse((moon[0] - r, moon[1] - r, moon[0] + r, moon[1] + r),
                                  fill=rgba(ICE, int(45 + 25 * math.sin(2 * math.pi * t))))
        f.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
        fx_layer = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        d = ImageDraw.Draw(fx_layer)
        for k in range(F):  # fireflies rise once per loop, drift and twinkle
            y = (fy[k] - t * (BH + 40)) % (BH + 40) - 20
            x = fx[k] + 18 * math.sin(2 * math.pi * t + fph[k])
            a = int(120 + 135 * (0.5 + 0.5 * math.sin(2 * math.pi * 3 * t + fph[k])))
            s = fsz[k]
            d.ellipse((x - s, y - s, x + s, y + s), fill=rgba(WARM[fcol[k]], a))
        for k in range(P):  # golden petals tumbling down-left
            y = (py[k] + t * (BH + 60)) % (BH + 60) - 30
            x = (px[k] - t * 260) % BW
            ang = 2 * math.pi * t * 2 + pph[k]
            pts = [(x + 11 * math.cos(ang + a_) * (1 if j % 2 == 0 else 0.45),
                    y + 11 * math.sin(ang + a_) * (1 if j % 2 == 0 else 0.45))
                   for j, a_ in enumerate((0, math.pi / 2, math.pi, 3 * math.pi / 2))]
            d.polygon(pts, fill=rgba(GOLD, 220))
        if 0.12 <= t < 0.3:  # shooting star, top right towards the moon
            u = (t - 0.12) / 0.18
            hx, hy = 1460 - 520 * u, 18 + 70 * u
            for j in range(26):
                tx, ty = hx + j * 7.5, hy - j * 1.0
                d.ellipse((tx - 3 + j * 0.1, ty - 3 + j * 0.1, tx + 3 - j * 0.1, ty + 3 - j * 0.1),
                          fill=rgba(LACE, int(255 * (1 - j / 26) * (1 - abs(u - 0.5)))))
            sparkle(d, hx, hy, 12, LACE, int(255 * (1 - abs(u - 0.5))))
        f.alpha_composite(blur_glow(fx_layer, 6, 1.6))
        f.alpha_composite(fx_layer)
        f.alpha_composite(over)
        frames.append(f.convert("RGB"))
    return frames


def banner(n=36, fps=9):
    frames = banner_frames(n)  # one 4 s loop; fewer frames keep the GIF under ~4 MB
    save(frames[0].convert("RGBA"), "banner.jpg", quality=92)
    # GIF via ffmpeg: one palette for the whole loop and only the changed rectangle per frame,
    # which keeps the night-sky gradients from flickering and the file small
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(frames):
            f.save(Path(tmp) / f"f{i:03d}.png")
        out = OUT / "banner.gif"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", str(Path(tmp) / "f%03d.png"),
                        "-vf", "split[a][b];[a]palettegen=max_colors=256:stats_mode=full[p];"
                               "[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                        "-loop", "0", str(out)], check=True)
    print(f"banner.gif: {BW}x{BH}, {len(frames)} frames, {out.stat().st_size / 1024:.0f} KB")


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
