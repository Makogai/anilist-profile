"""S rank ("SPECIAL"): the top tier of the waifu collection, in the spirit of Shoob's animated S cards.

An S card is rigged instead of only "alive". Codex paints the art plus four pixel-aligned twins in art/live/:
  waifu-<key>-matte.png   the girl on flat chroma green, keyed to her exact silhouette
  waifu-<key>-plate.png   the scenery with her removed, revealed wherever she moves
  waifu-<key>-blink.png   eyes closed
  waifu-<key>-parts.png   one flat colour per part (hair, skin, clothes, headdress/ribbon, horn, rose)
From those the rig finds her eyes, face, hair, ribbon and raised hand. Every frame it tilts and turns her head,
lets the hair tips and ribbon follow a beat later, waves the hand from the wrist and the forearm, breathes and
blinks. The scenery drifts behind her (parallax) under god rays and a turning magic circle, her horn and rose
glow, a moonlit rim light runs down her outline, and her head breaks out over the top of the frame.

The frame is cut crystal: holographic facets that flash as the light runs round the card, gold keylines,
orbiting comets, lightning crackling along the border, sapphire corner gems, a prismatic aura with rays and a
hexagonal S crest. Everything renders at twice the size of the other cards; waifus.card() saves both sizes.

Run through waifus.py:  python build/waifus.py rem-s
"""
import math
import zlib

import cv2
import numpy as np
from PIL import Image, ImageDraw

import waifus as Wf
from animated import shine_band
from common import (ART, GOLD, ICE, LACE, LILAC, MAGENTA, VOID, blur_glow, cover, draw_text, font, gradient,
                    mix, rgba, sparkle, text_mask)
from live import Animator, blink_amount, ellipse_mask

over, over_img, ramp, hsv = Wf.over, Wf.over_img, Wf.ramp, Wf.hsv

K = 2                                    # rendered at twice the size of the other cards
CW, CH, M, RAD = Wf.CW * K, Wf.CH * K, Wf.M * K, Wf.RAD * K
BW = 20 * K                              # wider border than the other ranks, for the crystal facets
SW, SH = CW + 2 * M, CH + 2 * M
AX, AY = M + BW - 2, M + BW - 2          # art window, with 2 px tucked under the border
AW, AH = CW - 2 * BW + 4, CH - 2 * BW + 4
HEAD_Y = M - 34                          # where the top of her head lands: above the card, in the aura
PRISM_S = [(0, LACE), (0.35, ICE), (0.7, LILAC), (1, MAGENTA)]
VIOLET_GLOW = (150, 110, 255)

# ---------------------------------------------------------------- card geometry (as in waifus.py, at 2x)

YY, XX = np.mgrid[0:SH, 0:SW].astype(np.float32)
_qx = np.abs(XX - SW / 2) - (CW / 2 - RAD)
_qy = np.abs(YY - SH / 2) - (CH / 2 - RAD)
SDF = np.hypot(np.maximum(_qx, 0), np.maximum(_qy, 0)) + np.minimum(np.maximum(_qx, _qy), 0) - RAD
CARD = np.clip(0.5 - SDF, 0, 1)
ART_M = np.clip(-(SDF + BW) + 0.5, 0, 1)
BORDER = CARD * (1 - ART_M)
OUTSIDE = np.clip(SDF, 0, None)
U = np.clip(-SDF / BW, 0, 1)
BEVEL = 0.55 + 0.5 * (1 - np.abs(2 * U - 1)) ** 0.6
ANG = (np.arctan2((YY - SH / 2) / CH, (XX - SW / 2) / CW) / (2 * math.pi)) % 1
ANG_TRUE = np.arctan2(YY - SH / 2, XX - SW / 2)
DIAG = np.clip((XX - M) / CW * 0.6 + (YY - M) / CH * 0.4, 0, 1)
KEY_OUT = np.exp(-((-SDF - 3.5) / 1.8) ** 2) * CARD          # gold keyline on the outer edge
KEY_IN = np.exp(-((-SDF - (BW - 3.5)) / 1.8) ** 2) * CARD    # platinum keyline on the inner edge
MIDLINE = np.exp(-((U - 0.5) / 0.28) ** 2) * BORDER          # where the comets run
_wy = np.clip((YY[:, :1] - AY) / AH, 0, 1)                   # darkening under the name area
SHADE = np.interp(_wy, [0, 0.6, 0.8, 1], [0, 0, 0.8, 0.98]).astype(np.float32)[..., None]


def outline(inset):
    """Ordered points (about 1 px apart) along the card outline moved `inset` px inwards (negative: outwards)."""
    m = (SDF <= -inset).astype(np.uint8)
    return max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=len)[:, 0, :].astype(
        np.float32)


def normals(pts):
    """Outward unit normals of a closed outline."""
    tan = np.roll(pts, -4, axis=0) - np.roll(pts, 4, axis=0)
    n = np.stack([tan[:, 1], -tan[:, 0]], axis=1)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
    probe = np.clip(pts + n * 6, 0, [SW - 1, SH - 1]).astype(int)
    return n if SDF[probe[:, 1], probe[:, 0]].mean() > 0 else -n


MID = outline(BW / 2)        # centre line of the border
MID_N = normals(MID)
HALO = outline(-26)          # just outside the card, for orbiting sparkles


def facets(n=130, seed=11):
    """Voronoi cells over the border: each border pixel's cell, the cell seeds, and the distance to the cell
    edge (for the dark seams between facets)."""
    rng = np.random.default_rng(seed)
    seeds = MID[np.sort(rng.choice(len(MID), n, replace=False))] + rng.normal(0, BW * 0.2, (n, 2))
    ys, xs = np.nonzero(BORDER > 0.01)
    d1 = np.full(len(xs), np.inf, np.float32)
    d2 = d1.copy()
    cell = np.zeros(len(xs), np.int32)
    for k, (px, py) in enumerate(seeds):
        d = (xs - px) ** 2 + (ys - py) ** 2
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        cell = np.where(closer, k, cell)
        d1 = np.where(closer, d, d1)
    return ys, xs, cell, seeds, np.sqrt(d2) - np.sqrt(d1)


FY, FX, FCELL, FSEEDS, FEDGE = facets()
_frng = np.random.default_rng(5)
CELL_HUE = _frng.uniform(0, 0.3, len(FSEEDS))
CELL_TONE = _frng.uniform(0.35, 1.0, len(FSEEDS))
CELL_ANG = ANG[np.clip(FSEEDS[:, 1].astype(int), 0, SH - 1), np.clip(FSEEDS[:, 0].astype(int), 0, SW - 1)]
SEAM = np.exp(-(FEDGE / 1.6) ** 2)


def angdist(a, b):
    d = np.abs((a - b) % 1)
    return np.minimum(d, 1 - d)


CRYSTAL = [(0, ICE), (0.25, (90, 150, 255)), (0.5, (150, 100, 255)), (0.75, MAGENTA), (1, ICE)]


def crystal_border(t):
    """Facet colours for one frame: ice-to-magenta crystal running round the card, every facet its own depth,
    flashing white as the light passes; bright seams between facets catch the light like cut edges."""
    fl = np.exp(-(angdist(CELL_ANG, t) / 0.04) ** 2) + 0.7 * np.exp(-(angdist(CELL_ANG, t + 0.5) / 0.04) ** 2)
    f = np.clip(fl[FCELL], 0, 1)[:, None]
    base = ramp((CELL_HUE[FCELL] + ANG[FY, FX] * 2 + t) % 1, CRYSTAL)
    tone = CELL_TONE[FCELL][:, None]
    col = (np.array((22, 18, 60), np.float32) * (1 - tone) + base * tone) * BEVEL[FY, FX][:, None]
    col = col * (1 - f) + 255 * f
    col = col + (255 - col) * (SEAM[:, None] * (0.3 + 0.6 * f))
    out = np.zeros((SH, SW, 3), np.float32)
    out[FY, FX] = np.clip(col, 0, 255)
    return out


# ---------------------------------------------------------------- ornaments

def gem(r, light=(185, 230, 255), dark=(25, 55, 150)):
    """Octagonal cut gem lit from the top left, supersampled for clean facets."""
    s = 4
    R = r * s
    size = 2 * R + 4 * s
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2

    def ring(rr):
        return [(c + rr * math.cos(math.radians(22.5 + 45 * k)), c + rr * math.sin(math.radians(22.5 + 45 * k)))
                for k in range(8)]

    o, i_ = ring(R), ring(R * 0.55)
    for k in range(8):
        shade = 0.5 + 0.5 * math.cos(math.radians(45 + 45 * k) - math.radians(225))
        d.polygon([o[k], o[(k + 1) % 8], i_[(k + 1) % 8], i_[k]], fill=rgba(mix(dark, light, shade)))
    d.polygon(i_, fill=rgba(mix(light, (255, 255, 255), 0.35)))
    d.polygon(o, outline=rgba(GOLD), width=2 * s)
    d.line([i_[4], i_[5]], fill=rgba(LACE), width=2 * s)
    return img.resize((size // s, size // s), Image.LANCZOS)


def crest(h):
    """Hexagonal S crest: gold rim, dark plate, prismatic S. Returns the image and its mask (0..1)."""
    w, pad = int(h * 0.88), 26
    size = (w + 2 * pad, h + 2 * pad)

    def hexagon(i):
        return [(pad + w / 2, pad + i), (pad + w - i, pad + h / 4 + i / 2), (pad + w - i, pad + 3 * h / 4 - i / 2),
                (pad + w / 2, pad + h - i), (pad + i, pad + 3 * h / 4 - i / 2), (pad + i, pad + h / 4 + i / 2)]

    outer, inner = Image.new("L", size, 0), Image.new("L", size, 0)
    ImageDraw.Draw(outer).polygon(hexagon(0), fill=255)
    ImageDraw.Draw(inner).polygon(hexagon(9), fill=255)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    glow = Image.new("RGBA", size, rgba(ICE))
    glow.putalpha(outer)
    img.alpha_composite(blur_glow(glow, 12, 1.7))
    rim = gradient(*size, Wf.GOLD_METAL, "d")
    rim.putalpha(outer)
    img.alpha_composite(rim)
    plate = gradient(*size, [(0, (28, 14, 64)), (1, (74, 30, 118))], "v")
    plate.putalpha(inner)
    img.alpha_composite(plate)
    ImageDraw.Draw(img).polygon(hexagon(15), outline=rgba(ICE, 210), width=3)
    draw_text(img, (pad + w / 2, pad + h / 2 + 3), "S", font("bahn", int(h * 0.64), "Bold"), anchor="mm",
              gradient_stops=PRISM_S, glow=ICE, glow_radius=12, shadow=True)
    return img, np.asarray(outer, np.float32) / 255


def magic_circle(r):
    """Two L masks for a seal behind her head: the inner hexagram (6-fold) and an outer ring of rune ticks
    (24-fold). Rotating them by 60 and 15 degrees per loop keeps the loop seamless."""
    s = 2
    R, size = r * s, int(2 * r * s + 16)
    c = size / 2
    inner, outer = Image.new("L", (size, size), 0), Image.new("L", (size, size), 0)
    di, do = ImageDraw.Draw(inner), ImageDraw.Draw(outer)

    def circ(d, rr, w):
        d.ellipse((c - rr, c - rr, c + rr, c + rr), outline=255, width=int(w))

    circ(di, R * 0.76, 3 * s)
    circ(di, R * 0.72, 1 * s)
    circ(di, R * 0.36, 2 * s)
    for off in (0, 180):
        tri = [(c + R * 0.72 * math.sin(math.radians(off + 120 * k)), c - R * 0.72 * math.cos(math.radians(off + 120 * k)))
               for k in range(3)]
        di.polygon(tri, outline=255, width=2 * s)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        x, y = c + R * 0.76 * math.sin(a), c - R * 0.76 * math.cos(a)
        di.ellipse((x - R * 0.045, y - R * 0.045, x + R * 0.045, y + R * 0.045), outline=255, width=2 * s)
    circ(do, R * 0.98, 2 * s)
    circ(do, R * 0.85, 2 * s)
    for k in range(96):
        a = math.radians(k * 3.75)
        r0, r1 = R * 0.87, R * (0.96 if k % 4 == 0 else 0.91)
        do.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + r1 * math.sin(a), c - r1 * math.cos(a))],
                fill=255, width=s)
    for k in range(24):
        a = math.radians(k * 15 + 7.5)
        x, y = c + R * 0.915 * math.sin(a), c - R * 0.915 * math.cos(a)
        rr = R * 0.018
        do.polygon([(x, y - rr), (x + rr, y), (x, y + rr), (x - rr, y)], fill=255)
    return inner.resize((size // s, size // s), Image.LANCZOS), outer.resize((size // s, size // s), Image.LANCZOS)


# ---------------------------------------------------------------- the rig

PART_COLOURS = {"hair": (255, 0, 255), "skin": (255, 255, 0), "clothes": (0, 255, 255), "acc": (255, 0, 0),
                "horn": (255, 255, 255), "rose": (0, 0, 255), "bg": (0, 0, 0)}


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def blur(m, sigma):
    return cv2.GaussianBlur(m, (0, 0), sigma)


def dilate(m, px):
    return cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1)))


def key_green(rgb):
    """Alpha from the chroma-green twin: 0 on the flat green, 1 on her, soft across anti-aliased edges."""
    spill = rgb[..., 1] - np.maximum(rgb[..., 0], rgb[..., 2])
    a = 1 - np.clip((spill - 25) / 70, 0, 1)
    solid = (a > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(solid, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = st[1:, cv2.CC_STAT_AREA] > solid.size * 0.0005       # drop stray specks
    a = a * dilate(keep[lab].astype(np.float32), 3)
    holes = (a < 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(holes, connectivity=4)
    small = np.zeros(n, bool)
    small[1:] = st[1:, cv2.CC_STAT_AREA] < holes.size * 0.0002       # fill pinholes of green inside her
    return np.where(small[lab], 1.0, a).astype(np.float32)


def classify(rgb):
    """Flat-colour part map -> {part: 0/1 mask}; anti-aliased in-between colours belong to no part."""
    best = np.full(rgb.shape[:2], np.inf, np.float32)
    lab = np.full(rgb.shape[:2], -1, np.int8)
    for i, c in enumerate(PART_COLOURS.values()):
        d = ((rgb - np.array(c, np.float32)) ** 2).sum(axis=2)
        lab = np.where(d < best, i, lab)
        best = np.minimum(best, d)
    lab[best > 110 ** 2] = -1
    return {name: (lab == i).astype(np.float32) for i, name in enumerate(PART_COLOURS)}


def components(mask, min_frac):
    n, lab, st, cen = cv2.connectedComponentsWithStats((mask > 0.5).astype(np.uint8), connectivity=8)
    return [(lab == i, st[i], cen[i]) for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= mask.size * min_frac]


class Rig:
    """The layered, rigged character of one S card. Everything is in "placed" pixels: the art scaled to cover
    the art window plus `pop` rows above it, where her head breaks out of the frame."""

    def __init__(self, key):
        live = ART / "live"
        art_src = Image.open(ART / f"waifu-{key}.png").convert("RGB")

        def twin(kind):
            return Image.open(live / f"waifu-{key}-{kind}.png").convert("RGB").resize(art_src.size, Image.LANCZOS)

        matte = twin("matte")
        # how many rows above the window the art needs so the top of her head lands at HEAD_Y
        a_src = key_green(np.asarray(matte, np.float32))
        top = np.nonzero((a_src > 0.5).sum(axis=1) > 3)[0][0] / art_src.height
        self.pop = int(np.clip(round((AY - HEAD_Y + top * AH) / (1 - top)), 0, AY))
        self.size = PW, PH = AW, AH + self.pop

        def place(img):
            return np.asarray(cover(img, self.size, (0.5, 0.0)), np.float32)[..., :3]

        art, blink, self.plate = place(art_src), place(twin("blink")), place(twin("plate"))
        alpha = key_green(place(matte))
        # the matte is a repaint and can sit a few px off the art (by the fingers most), which drags slivers of
        # the old background along when she moves. The plate lines up with the art's background almost
        # exactly, so near her outline the difference from the plate decides instead.
        solid = (alpha > 0.5).astype(np.uint8)
        band = (dilate(solid, 10) > 0) & (cv2.erode(solid, np.ones((21, 21), np.uint8)) == 0)
        by_plate = np.clip((blur(np.abs(art - self.plate).mean(axis=2), 1) - 24) / 28, 0, 1)
        alpha = cv2.morphologyEx(np.where(band, by_plate, alpha).astype(np.float32), cv2.MORPH_OPEN,
                                 np.ones((3, 3), np.uint8))
        parts = {k: v * (alpha > 0.5) for k, v in classify(place(twin("parts"))).items()}
        self.yy = np.mgrid[0:PH, 0:PW][0].astype(np.float32)
        yy = self.yy
        print(f"  rig: pop {self.pop}px, matte vs art inside her: "
              f"{np.abs(place(matte) - art).mean(axis=2)[alpha > 0.95].mean():.1f} mean diff")

        # eyes: where the closed-eye twin differs; their spacing d sets the scale of the face
        diff = blur(np.abs(art - blink).mean(axis=2), 2)
        n, lab, st, cen = cv2.connectedComponentsWithStats((diff > diff.max() * 0.25).astype(np.uint8))
        best = (np.argsort(-st[1:, cv2.CC_STAT_AREA])[:2] + 1).tolist()
        (ex0, ey0), (ex1, ey1) = sorted(tuple(cen[i]) for i in best)
        d = self.d = math.hypot(ex1 - ex0, ey1 - ey0)
        fx, ey = (ex0 + ex1) / 2, (ey0 + ey1) / 2
        boxes = np.zeros_like(diff)
        for i in best:
            x, y, w, h = st[i, :4]
            boxes[max(0, y - h // 2):y + h + h // 2, max(0, x - w // 3):x + w + w // 3] = 1
        changed = np.clip((blur(diff, 3) - diff.max() * 0.05) / (diff.max() * 0.1), 0, 1)  # ignore twin noise
        eye = blur(dilate(changed * boxes, 6), 4)
        chin = ey + 0.95 * d
        self.pivot = (fx, ey + 1.35 * d)                 # the neck
        print(f"  rig: eyes at ({ex0:.0f},{ey0:.0f}) and ({ex1:.0f},{ey1:.0f}), spacing {d:.0f}px")

        # face = the skin component under the eyes; the raised hand = the highest other skin component
        comps = components(parts["skin"], 0.002)
        face = min(comps, key=lambda c: math.hypot(c[2][0] - fx, c[2][1] - (ey + 0.5 * d)))[0]
        others = [c for c in comps if c[0] is not face and abs(c[2][0] - fx) > 0.9 * d]
        self.arm = self.hand = None
        if others:
            m, s, _ = min(others, key=lambda c: c[1][cv2.CC_STAT_TOP])
            x, y, w, h = s[:4]
            bottom = y + h - 1
            wrist_y = y + 0.62 * h                     # fingers and palm take the top 60 %, the forearm the rest
            self.elbow = (np.nonzero(m[bottom])[0].mean(), bottom)
            self.wrist = (np.nonzero(m[int(wrist_y)])[0].mean(), wrist_y)
            soft = blur(dilate(m.astype(np.float32), 8), 6)
            self.arm = soft * smoothstep(bottom, bottom - 0.25 * h, yy)          # hand and forearm
            self.hand = soft * smoothstep(wrist_y + 0.08 * h, wrist_y - 0.04 * h, yy)
            print(f"  rig: raised hand {w}x{h} at ({x},{y}), wrist {self.wrist[1]:.0f}, elbow {bottom}")

        hair = parts["hair"]
        rows = np.nonzero(hair.sum(axis=1) > 2)[0]
        face_ell = ellipse_mask(art.shape, (fx, ey + 0.2 * d), (1.0 * d, 0.9 * d), 0.15 * d)
        self.tips = blur(hair, 3) * np.clip((yy - rows[0]) / (rows[-1] - rows[0]), 0, 1) ** 1.3 * (1 - 0.75 * face_ell)
        self.ribbon = blur(parts["acc"] * smoothstep(ey - 1.0 * d, ey + 0.4 * d, yy), 3)
        head = np.maximum.reduce([hair, parts["acc"] * (yy < ey + 1.2 * d), parts["horn"],
                                  face.astype(np.float32) * (yy < chin)])
        self.head = blur(dilate(head, 4), 5) * smoothstep(self.pivot[1], chin, yy)
        if self.arm is not None:
            self.head *= 1 - self.arm
        self.body = alpha * smoothstep(chin, chin + 0.8 * d, yy)
        xx = np.mgrid[0:PH, 0:PW][1].astype(np.float32)
        r2 = ((xx - fx) / (1.05 * d)) ** 2 + ((yy - ey - 0.3 * d) / (1.1 * d)) ** 2
        self.bulge = np.clip(1 - r2, 0, 1) ** 1.5        # head turn: features slide inside the face outline

        # glows that move with her: horn halo, rose halo, eye glints
        glint = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glint)
        for i in best:
            x, y, w, h = st[i, :4]
            sparkle(gd, x + 0.68 * w, y + 0.3 * h, int(0.1 * d), (255, 255, 255))
        self.glow = np.dstack([blur(parts["horn"], 0.07 * d), blur(parts["rose"], 0.1 * d),
                               blur(np.asarray(glint.getchannel("A"), np.float32) / 255, 1.2)]).astype(np.float32)
        self.char = np.dstack([art, alpha]).astype(np.float32)
        self.blink = np.dstack([blink, eye]).astype(np.float32)
        self.anim = Animator(self.char)
        self.rim_rows = np.linspace(0, 1, PH, dtype=np.float32)[:, None]

        # the moon (brightest large blob of the plate's upper part) anchors rays and the magic circle
        lum = self.plate[: int(PH * 0.6)].mean(axis=2)
        moon = max(components((lum > lum.max() * 0.72).astype(np.float32), 0.001), key=lambda c: c[1][4])
        x, y, w, h = moon[1][:4]
        self.moon, self.moon_r = (x + w / 2, y + h / 2), (w + h) / 4
        mm = np.zeros((PH, PW), np.float32)
        cv2.circle(mm, (int(x + w / 2), int(y + h / 2)), int(self.moon_r), 1.0, -1)
        self.moon_mask = blur(mm, 20)[..., None]
        yy_, xx_ = np.mgrid[0:PH, 0:PW].astype(np.float32)
        self.moon_dist = np.hypot(xx_ - self.moon[0], yy_ - self.moon[1])
        self.moon_ang = np.arctan2(yy_ - self.moon[1], xx_ - self.moon[0])
        self.seal = magic_circle(int(self.moon_r * 1.12))

    def frame(self, t):
        """Her layer for loop phase t: (rgb, alpha, additive glow), all PH x PW."""
        a, d = self.anim, self.d
        tau = 2 * math.pi
        a.my -= (a.yy - a.yy.max()) * 0.007 * math.sin(tau * t) * self.body           # breathing
        if self.arm is not None:                                                        # wave
            a.rotate(self.arm, self.elbow, 2.2 * math.sin(tau * 2 * t - 0.6))
            a.rotate(self.hand, self.wrist, 9 * math.sin(tau * 2 * t))
        a.sway(self.ribbon, 2 * t, 0.035 * d, wavelength=0.9 * d, along=(0.6, 0.6))      # ribbon tails flutter
        a.sway(self.tips, t - 0.12, 0.03 * d, wavelength=1.6 * d)                      # hair follows, late
        a.mx -= 0.028 * d * math.sin(tau * t + 1.1) * self.bulge                       # head turn
        a.rotate(self.head, self.pivot, 2.0 * math.sin(tau * t))                       # head tilt
        char, blink, glow = a.render_many(self.char, self.blink, self.glow)
        rgb, alpha = char[..., :3], np.clip(char[..., 3], 0, 1)
        k = blink_amount(t, 0.47, 0.085)
        if k > 0:
            m = (blink[..., 3:4] * k)
            rgb = rgb * (1 - m) + blink[..., :3] * m
        # moonlit rim light running down her outline
        rim = np.clip(alpha - blur(alpha, 0.03 * d), 0, 1) * 2.4
        light = np.clip(1.3 - self.rim_rows * 1.5, 0.15, 1)
        col = ramp(0.5 + 0.5 * np.sin(tau * (t - self.rim_rows[:, 0] * 1.4)), [(0, ICE), (0.5, (205, 195, 255)),
                                                                                (1, (255, 175, 230))])[:, None]
        rgb = rgb + (rim * light[:, 0:1])[..., None] * col * 0.6
        pulse = 0.5 + 0.5 * math.sin(tau * 2 * t)
        add = (glow[..., 0:1] * (0.3 + 0.4 * pulse) * np.array((150, 215, 255), np.float32)
               + glow[..., 1:2] * (0.45 + 0.4 * math.sin(tau * t + 2)) * np.array((60, 120, 255), np.float32) * 1.6)
        g = max(0.0, math.sin(math.pi * (t - 0.2) / 0.16)) if 0.2 <= t < 0.36 else 0.0
        if g:
            add = add + glow[..., 2:3] * g * 255
        return np.clip(rgb, 0, 255), alpha, add

    def background(self, t, motes):
        """Scenery behind her for loop phase t: drifting plate, breathing moonlight, rays and the seal."""
        tau = 2 * math.pi
        s = 1.016 + 0.01 * math.sin(tau * t)
        dx, dy = -0.04 * self.d * math.sin(tau * t + 1.1), 0.015 * self.d * math.cos(tau * t)
        cx, cy = self.moon
        m = np.float32([[s, 0, (1 - s) * cx + dx], [0, s, (1 - s) * cy + dy]])
        bg = cv2.warpAffine(self.plate, m, self.size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        bg = bg + self.moon_mask * (0.03 + 0.05 * math.sin(tau * t)) * 255
        rays = (0.5 + 0.5 * np.cos(14 * self.moon_ang + tau * t)) ** 10 * np.exp(-self.moon_dist / (1.4 * self.moon_r))
        bg = bg + (rays * 0.22)[..., None] * np.array((170, 215, 255), np.float32)
        inner, outer = self.seal
        size = inner.size[0]
        x0, y0 = int(cx - size / 2), int(cy - size / 2)
        seal = (np.asarray(inner.rotate(-60 * t, Image.BICUBIC), np.float32)
                + np.asarray(outer.rotate(15 * t, Image.BICUBIC), np.float32)) / 255 * (0.36 + 0.16 * math.sin(tau * 2 * t))
        layer = np.zeros((self.size[1], self.size[0]), np.float32)
        ys, xs = slice(max(0, y0), min(self.size[1], y0 + size)), slice(max(0, x0), min(self.size[0], x0 + size))
        layer[ys, xs] = seal[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
        glow = blur(layer, 4)
        bg = bg + (layer + glow * 1.5)[..., None] * np.array((175, 225, 255), np.float32)
        return np.clip(bg + motes, 0, 255)


# ---------------------------------------------------------------- static overlay: crest, gems, text

_c = M + RAD - (RAD - BW / 2) / math.sqrt(2)   # corner of the border centre line, at 45 degrees
# three corners (the crest takes the top left), then the middle of each side
GEMS = [(SW - _c, _c), (_c, SH - _c), (SW - _c, SH - _c), (M + BW / 2, SH / 2), (SW - M - BW / 2, SH / 2)]
CREST_C = (M + BW / 2 + 22, M + BW / 2 + 62)


def overlay(key, name, jp, series, rank):
    """Everything that does not move, plus masks of the crest and the name for their light sweeps."""
    top = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    d.rounded_rectangle((M + BW, M + BW, M + CW - BW - 1, M + CH - BW - 1), RAD - BW, outline=rgba(LACE, 170),
                        width=3)
    for i, (x, y) in enumerate(GEMS):
        g = gem(30 if i < 3 else 20)
        top.alpha_composite(g, (int(x - g.width / 2), int(y - g.height / 2)))
    cimg, cmask = crest(150)
    cx, cy = int(CREST_C[0] - cimg.width / 2), int(CREST_C[1] - cimg.height / 2)
    top.alpha_composite(cimg, (cx, cy))
    crest_m = np.zeros((SH, SW), np.float32)
    crest_m[cy:cy + cimg.height, cx:cx + cimg.width] = cmask

    x = M + BW + 34
    draw_text(top, (x + 4, M + CH - 318), series, font("bahn", 56, "SemiBold"), fill=(205, 228, 255), anchor="ls",
              tracking=4, shadow=True)
    nf = font("bahn", 168, "Bold")
    name_xy = (x, M + CH - 168)
    draw_text(top, name_xy, name, nf, anchor="ls", tracking=12, gradient_stops=PRISM_S, glow=ICE, glow_radius=26)
    name_m = np.asarray(text_mask((SW, SH), name_xy, name, nf, "ls", 12), np.float32) / 255
    draw_text(top, (M + CW - BW - 40, M + CH - 172), jp, font("serifjp", 92, "Bold"), fill=LACE, anchor="rs",
              glow=ICE, glow_radius=14, shadow=True)
    Wf.tokens(top, x + 2, M + CH - 100, Wf.VARIANT_OF.get(key, key), rank, size=64, gap=74)
    draw_text(top, (M + CW - BW - 40, M + CH - 78), Wf.RANKS[rank]["name"], font("bahn", 52, "Bold"), anchor="rs",
              tracking=8, gradient_stops=[(0, ICE), (0.5, LILAC), (1, MAGENTA)], glow=VIOLET_GLOW, glow_radius=10)
    return top, crest_m, name_m


# ---------------------------------------------------------------- lightning

def bolt(d, rng, start, length, jitter):
    """One lightning arc crackling along the border centre line, sometimes forking out into the aura: straight
    jagged legs between kinks, plus fine crackle."""
    n = max(3, length // 26)
    kinks = rng.normal(0, jitter, n + 1)
    kinks[0] = kinks[-1] = 0                                 # pinned to the border at both ends
    steps = np.arange(0, length, 6)
    off = np.interp(steps, np.linspace(0, length, n + 1), kinks) + rng.normal(0, 1.6, len(steps))
    idx = (start + steps) % len(MID)
    pts = MID[idx] + MID_N[idx] * off[:, None]
    path = [tuple(p) for p in pts]
    d.line(path, fill=rgba((120, 200, 255), 170), width=14)
    d.line(path, fill=rgba((255, 255, 255), 255), width=4)
    if rng.random() < 0.75:                                  # a fork reaching outwards
        j = rng.integers(len(idx))
        p, n = pts[j], MID_N[idx[j]]
        fork = [tuple(p)]
        for _ in range(4):
            p = p + n * rng.uniform(10, 18) + rng.normal(0, 10, 2)
            fork.append(tuple(p))
        d.line(fork, fill=rgba((170, 140, 255), 160), width=10)
        d.line(fork, fill=rgba((255, 255, 255), 235), width=3)


# ---------------------------------------------------------------- frames

def bloom(f, img: Image.Image, radius, strength=1.0):
    """Add a blurred RGBA layer as light. The blur is premultiplied, so the transparent black around particles
    doesn't bleed in and grey them out (as a plain RGBA blur does), and light never darkens what is under it."""
    a = np.asarray(img, np.float32)
    k = a[..., 3] / 255
    pre = cv2.GaussianBlur(a[..., :3] * k[..., None], (0, 0), radius) * strength
    f[..., :3] = np.minimum(255, f[..., :3] + pre)
    f[..., 3] = np.maximum(f[..., 3], np.clip(cv2.GaussianBlur(k, (0, 0), radius) * strength, 0, 1))


def card_frames(key, name, jp, series, rank):
    r = Wf.RANKS[rank]
    rig = Rig(key)
    top, crest_m, name_m = overlay(key, name, jp, series, rank)
    PW, PH = rig.size
    y0 = AY - rig.pop
    popmask = (1 - smoothstep(AY + 2, AY + 14, YY))          # rows where her head may cover the frame
    n = r["frames"]
    rng = np.random.default_rng(zlib.crc32(key.encode()))
    motes = [(rng.uniform(0, PW), rng.uniform(0, 1), rng.uniform(0.6, 1.3), rng.uniform(0, 1), rng.uniform(3, 7))
             for _ in range(26)]
    petals = [(rng.uniform(0, SW), rng.uniform(0, 1), rng.uniform(0, 1), rng.integers(0, 3)) for _ in range(16)]
    bokeh = [(rng.uniform(M, SW - M), rng.uniform(0, 1), rng.uniform(26, 54), rng.integers(0, 3)) for _ in range(7)]
    twinkles = [(rng.uniform(M + 60, M + CW - 60), rng.uniform(M + 120, M + CH * 0.6), rng.uniform(0, 1),
                 rng.uniform(16, 30)) for _ in range(9)]
    orbit = [(rng.uniform(0, 1), rng.uniform(0, 1)) for _ in range(28)]
    frames = []
    for i in range(n):
        t = i / n
        tau = 2 * math.pi
        pulse = 0.5 + 0.5 * math.sin(tau * t)
        f = np.zeros((SH, SW, 4), np.float32)

        # prismatic aura and rotating rays around the card
        out = OUTSIDE > 0
        rays = (0.5 + 0.5 * np.cos(20 * ANG_TRUE - tau * t)) ** 10 * np.exp(-OUTSIDE / (34 * K)) * out
        over(f, hsv(ANG + t, 0.55, 1.0), np.exp(-OUTSIDE / (17 * K)) * out * (0.68 + 0.27 * pulse) + rays * 0.6)

        # the window: scenery, then her
        ml = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        md = ImageDraw.Draw(ml)
        for x, y_, spd, ph, s in motes:                     # ice motes rising behind her
            y = PH - ((y_ + t * spd) % 1) * PH
            al = int(220 * (0.5 + 0.5 * math.sin(tau * (2 * t + ph))))
            if s > 5.5:
                sparkle(md, x, y, int(s * 2.2), (200, 230, 255), al)
            else:
                md.ellipse((x - s / 2, y - s / 2, x + s / 2, y + s / 2), fill=rgba((170, 210, 255), al))
        ma = np.asarray(blur_glow(ml, 4, 1.5), np.float32)
        ma2 = np.asarray(ml, np.float32)
        motes_rgb = ma[..., :3] * ma[..., 3:4] / 255 + ma2[..., :3] * ma2[..., 3:4] / 255
        bg = rig.background(t, motes_rgb)
        rgb, alpha, add = rig.frame(t)
        win = np.clip(bg * (1 - alpha[..., None]) + rgb * alpha[..., None] + add, 0, 255)
        canvas = np.zeros((SH, SW, 3), np.float32)
        canvas[y0:y0 + PH, AX:AX + PW] = win
        canvas = canvas * (1 - SHADE) + np.array(VOID, np.float32) * SHADE
        over(f, canvas, ART_M)

        # crystal border, keylines, comets
        over(f, crystal_border(t), BORDER)
        gold = ramp(0.5 + 0.5 * np.cos(tau * (DIAG * 2 - t)), Wf.GOLD_METAL)
        over(f, gold, KEY_OUT)
        over(f, ramp(0.5 + 0.5 * np.cos(tau * (DIAG * 2 - t) + 1), [(0, (190, 205, 255)), (1, (255, 255, 255))]),
             KEY_IN)
        da = np.minimum.reduce([(ANG - (t + off)) % 1 for off in (0, 1 / 3, 2 / 3)])
        comet = np.exp(-(np.minimum(da, 1 - da) / 0.008) ** 2) + np.exp(-da / 0.06) * (da < 0.5) * 0.8
        over(f, ramp(np.clip(da * 10, 0, 1), [(0, (255, 255, 255)), (0.3, ICE), (0.7, LILAC), (1, MAGENTA)]),
             np.clip(comet, 0, 1) * MIDLINE)

        # holo foil band and a shine sweep over the art
        hue = (XX * 0.8 + YY * 0.5) / (420 * K) + t
        pos = -260 * K + (SW + SH * 0.5 + 520 * K) * t
        over(f, hsv(hue, 0.6, 1.0), ART_M * np.exp(-((XX + YY * 0.5 - pos) / (170 * K)) ** 2) * 0.16)
        if 0.55 <= t < 0.85:
            u = (t - 0.55) / 0.3
            band = np.asarray(shine_band((SW, SH), -300 * K + (SW + SH * 0.35 + 600 * K) * u, 80 * K, 0.35,
                                         strength=150), np.float32)
            over(f, band[..., :3], band[..., 3] / 255 * CARD)

        # ornaments and text, then light running through the crest and the name
        over_img(f, top)
        if 0.05 <= t < 0.3:
            u = (t - 0.05) / 0.25
            cpos = CREST_C[0] - 140 + 280 * u
            over(f, (255, 255, 255), crest_m * np.exp(-((XX + (YY - CREST_C[1]) * 0.5 - cpos) / 18) ** 2) * 0.85)
        if 0.6 <= t < 0.9:
            u = (t - 0.6) / 0.3
            npos = M + BW - 60 + 520 * u
            over(f, (255, 255, 255), name_m * np.exp(-((XX + (YY - M - CH) * 0.4 - npos) / 30) ** 2) * 0.9)

        # her head breaking out over the top of the frame
        pop_rgb = np.zeros((SH, SW, 3), np.float32)
        pop_a = np.zeros((SH, SW), np.float32)
        pop_rgb[y0:y0 + PH, AX:AX + PW] = rgb
        pop_a[y0:y0 + PH, AX:AX + PW] = alpha
        over(f, pop_rgb, pop_a * popmask)

        # front effects: lightning, petals, bokeh, twinkles, gem glints, orbiting sparkles
        fx = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        d = ImageDraw.Draw(fx)
        brng = np.random.default_rng(1000 + i)
        burst = 0.12 <= t < 0.26 or 0.62 <= t < 0.72
        for _ in range(brng.integers(1, 4) if burst else int(brng.random() < 0.3)):
            bolt(d, brng, brng.integers(len(MID)), brng.integers(140, 420), 9)
        cols = [(150, 190, 255), (255, 175, 215), (240, 240, 255)]
        for x0, y_, ph, ci in petals:
            y = (y_ + t) % 1 * (SH + 80) - 40
            x = (x0 - t * 240 + 36 * math.sin(tau * (t + ph))) % SW
            ang = tau * (t * 2 + ph)
            pts = [(x + 18 * math.cos(ang + a_) * (1 if j % 2 == 0 else 0.42),
                    y + 18 * math.sin(ang + a_) * (1 if j % 2 == 0 else 0.42))
                   for j, a_ in enumerate((0, math.pi / 2, math.pi, 3 * math.pi / 2))]
            d.polygon(pts, fill=rgba(cols[ci], 225))
        for x, y, ph, s in twinkles:
            al = max(0.0, math.sin(tau * (2 * t + ph)))
            if al > 0.05:
                sparkle(d, x, y, int(s * (0.6 + 0.4 * al)), LACE, int(255 * al))
        for j, (gx, gy) in enumerate(GEMS):
            al = max(0.0, math.sin(tau * (t + j / len(GEMS))))
            if al > 0.6:
                sparkle(d, gx + 8, gy - 8, int(34 * (al - 0.4)), (255, 255, 255), int(255 * (al - 0.4) / 0.6))
        for u0, ph in orbit:
            p = HALO[int(((u0 + t) % 1) * len(HALO)) % len(HALO)]
            al = 0.5 + 0.5 * math.sin(tau * (3 * t + ph))
            sparkle(d, p[0], p[1], int(6 + 10 * al), (220, 235, 255), int(80 + 175 * al))
        bk = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bk)
        for x, y_, rr, ci in bokeh:                          # out-of-focus orbs drifting in front
            y = SH - ((y_ + t * 0.5) % 1) * (SH + 2 * rr) + rr
            bd.ellipse((x - rr, y - rr, x + rr, y + rr), fill=rgba([(120, 180, 255), (190, 150, 255), (255, 160, 220)][ci], 70))
        bloom(f, bk, 10)                                     # added as light, so they never darken her
        if fx.getbbox():
            bloom(f, fx, 6 * K, 1.5)
            over_img(f, fx)

        frames.append(Image.fromarray(np.clip(np.dstack([f[..., :3], f[..., 3:4] * 255]), 0, 255).astype(np.uint8),
                                      "RGBA"))
        print(f"  frame {i + 1}/{n}", end="\r")
    print()
    return frames
