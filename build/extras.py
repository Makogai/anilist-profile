"""Profile banner (AniList settings -> banner, 1700x330) and avatar (settings -> avatar).

AniList draws the avatar and username over the banner's lower-left, so that area stays calm.
"""
import numpy as np
from PIL import Image, ImageDraw

from common import (ART, ICE, ICE_VIOLET, VOID, black_to_alpha, blur_glow, cover, darken, gradient,
                    particles, rgba, save)


def banner():
    w, h = 1700, 330
    # night sky across the strip, with the hero art scaled down on the right so Rem's whole head fits
    img = darken(cover(Image.open(ART / "bg-night.png").convert("RGBA"), (w, h), (0.5, 0.5)), 1.0)
    art = Image.open(ART / "hero-rem.png").convert("RGBA")
    s = 0.58
    art = art.resize((round(art.width * s), round(art.height * s)), Image.LANCZOS)
    art = art.crop((0, round(235 * s), art.width, round(235 * s) + h))  # rows around her face
    fade = np.clip(np.linspace(0, 1, art.width) / 0.45, 0, 1)
    art.putalpha(Image.fromarray(np.tile((fade * 255).astype(np.uint8), (h, 1)), "L"))
    img.alpha_composite(art, (w - art.width, 0))
    img.alpha_composite(gradient(w, h, [(0, rgba(VOID, 0)), (0.6, rgba(VOID, 0)), (1, rgba(VOID, 130))], "v"))
    img.alpha_composite(particles((w, h), 60, 33, rmax=7))
    # chain only across the empty left part, fading out before Rem
    chain = Image.open(ART / "orn-morningstar.png").convert("RGB")
    band = chain.crop((0, 410, chain.width, 600)).resize((1100, round(190 * 1100 / chain.width)), Image.LANCZOS)
    band = black_to_alpha(np.asarray(band, np.float32))
    a = np.asarray(band.getchannel("A"), np.float32) * np.clip((1000 - np.arange(1100)) / 300, 0, 1)[None, :]
    band.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    img.alpha_composite(band, (0, 40))
    save(img, "banner.jpg", quality=90)


def avatar():
    s = 460
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    face = cover(Image.open(ART / "waifu-rem.png").convert("RGBA"), (s - 40, s - 40), (0.5, 0.15))
    m = Image.new("L", face.size, 0)
    ImageDraw.Draw(m).ellipse((0, 0, face.width - 1, face.height - 1), fill=255)
    face.putalpha(m)
    ring_l = Image.new("L", (s, s), 0)
    ImageDraw.Draw(ring_l).ellipse((10, 10, s - 11, s - 11), outline=255, width=12)
    ring = gradient(s, s, ICE_VIOLET, "d")
    ring.putalpha(ring_l)
    glow = Image.new("RGBA", (s, s), rgba(ICE))
    glow.putalpha(ring_l)
    img.alpha_composite(blur_glow(glow, 8, 1.4))
    img.alpha_composite(face, (20, 20))
    img.alpha_composite(ring)
    save(img, "avatar.png")


if __name__ == "__main__":
    banner()
    avatar()
