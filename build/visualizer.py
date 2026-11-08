"""Rem music visualizer, driven by the real spectrum of music.mp3.

  python build/visualizer.py loop   -> profile/nowplaying.webm  (muted ~12 s seamless loop, 1028 px wide,
                                       for AniList's webm() which always plays muted)
  python build/visualizer.py full   -> export/rem-visualizer-full.mp4  (1920x1080 with audio, for YouTube;
                                       not committed: it contains the song)
"""
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from common import (ART, BLUE, ICE, ICE_VIOLET, INDIGO, LACE, LILAC, MAGENTA, OUT, ROOT, SILVER, VIOLET,
                    VOID, blur_glow, card_frame, cover, darken, draw_text, font, gradient, mix, rgba, rounded_mask,
                    sparkle, vignette)

SR = 44100
FPS = 24
BANDS = 48


def load_audio():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(ROOT / "music.mp3"), "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def band_edges():
    return np.geomspace(45, 14000, BANDS + 1)


def spectrum_at(x, t, win=4096):
    c = int(t * SR)
    seg = x[max(0, c - win // 2): c + win // 2]
    if len(seg) < win:
        seg = np.pad(seg, (0, win - len(seg)))
    mag = np.abs(np.fft.rfft(seg * np.hanning(win)))
    freqs = np.fft.rfftfreq(win, 1 / SR)
    e = band_edges()
    out = np.empty(BANDS)
    for b in range(BANDS):
        sel = (freqs >= e[b]) & (freqs < e[b + 1])
        out[b] = mag[sel].mean() if sel.any() else mag[np.argmin(np.abs(freqs - e[b]))]
    return 20 * np.log10(out + 1e-6)


def analyse(x, times):
    raw = np.array([spectrum_at(x, t) for t in times])
    lo = np.percentile(raw, 12, axis=0)
    hi = np.percentile(raw, 99, axis=0)
    v = np.clip((raw - lo) / np.maximum(hi - lo, 1e-3), 0, 1) ** 1.4
    # attack fast, release slow so bars stay readable instead of flickering
    out = np.zeros_like(v)
    prev = v[0]
    for i, cur in enumerate(v):
        prev = np.where(cur > prev, prev + (cur - prev) * 0.7, prev + (cur - prev) * 0.22)
        out[i] = prev
    return out


def tempo_and_start(x, lo=66.0, hi=108.0):
    """Beat period from onset autocorrelation, and a loop start on a strong onset in the chorus."""
    hop = 512
    seg = x[int(lo * SR): int(hi * SR)]
    frames = np.lib.stride_tricks.sliding_window_view(seg, 2048)[::hop]
    spec = np.abs(np.fft.rfft(frames * np.hanning(2048), axis=1))
    flux = np.maximum(np.diff(np.log1p(spec), axis=0), 0).sum(axis=1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fr = SR / hop
    lags = np.arange(int(fr * 60 / 180), int(fr * 60 / 70))
    ac = np.array([np.dot(flux[:-l], flux[l:]) for l in lags])
    period = lags[np.argmax(ac)] / fr
    # strongest onset within the first 20 s of the window, so the loop sits inside the chorus
    i0 = int(np.argmax(flux[: int(20 * fr)]))
    return period, lo + i0 / fr


# ---------------------------------------------------------------- drawing

class Scene:
    def __init__(self, w, h, duration, title="MAKOGAI'S FAVORITE SONG", framed=False):
        self.w, self.h, self.s = w, h, h / 620
        self.duration, self.title = duration, title
        s = self.s
        # video has no alpha, so the rounded card frame of the other panels is baked in, with the
        # corners filled in AniList's dark-theme box colour
        self.overlay = None
        if framed:
            self.overlay = card_frame((w, h), 32, 4, ICE_VIOLET, BLUE, inset=6)
            corners = Image.new("RGBA", (w, h), (21, 31, 46, 255))
            corners.putalpha(rounded_mask((w, h), 40).point(lambda v: 255 - v))
            self.overlay.alpha_composite(corners)
        art = Image.open(ART / "hero-rem.png").convert("RGBA")
        bg = darken(cover(art, (w, h), (0.55, 0.42)), 0.5).filter(ImageFilter.GaussianBlur(5 * s))
        bg.alpha_composite(gradient(w, h, [(0, rgba(VOID, 120)), (0.5, rgba(INDIGO, 20)), (1, rgba(VOID, 170))], "v"))
        self.bg = vignette(bg, 0.6)
        self.cx, self.cy = w // 2, int(h * 0.48)
        r = int(120 * s)
        face = cover(Image.open(ART / "waifu-rem.png").convert("RGBA"), (2 * r, 2 * r), (0.5, 0.16))
        m = Image.new("L", (2 * r, 2 * r), 0)
        ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
        face.putalpha(m)
        self.face, self.r = face, r
        rng = np.random.default_rng(7)
        n = 90
        self.p = dict(x=rng.uniform(0, w, n), y=rng.uniform(0, h, n), d=rng.choice([1, 1, 2], n),
                      size=rng.uniform(1.5, 4, n) * s, ph=rng.uniform(0, 2 * math.pi, n),
                      star=rng.random(n) < 0.3, col=rng.integers(0, 4, n))

    def label(self, img, t_abs):
        s = self.s
        x0, y0, lw, lh = int(36 * s), int(30 * s), int(470 * s), int(96 * s)
        plate = gradient(lw, lh, [(0, rgba(INDIGO, 210)), (1, rgba(VOID, 150))], "h")
        plate.putalpha(Image.fromarray(np.minimum(np.asarray(plate.getchannel("A")),
                                                  np.asarray(rounded_mask((lw, lh), int(18 * s)))), "L"))
        img.alpha_composite(plate, (x0, y0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((x0, y0, x0 + lw, y0 + lh), int(18 * s), outline=rgba(ICE, 150), width=max(1, int(2 * s)))
        # little equaliser icon
        for k, hh in enumerate((18, 30, 22)):
            bx = x0 + int((24 + k * 11) * s)
            d.rounded_rectangle((bx, y0 + int((44 - hh / 2) * s), bx + int(7 * s), y0 + int((44 + hh / 2) * s)),
                                int(3 * s), fill=rgba(ICE))
        draw_text(img, (x0 + int(70 * s), y0 + int(38 * s)), "NOW PLAYING", font("bahn", int(24 * s), "SemiBold"),
                  fill=ICE, anchor="ls", tracking=int(5 * s), shadow=False)
        draw_text(img, (x0 + int(70 * s), y0 + int(66 * s)), self.title, font("bahn", int(24 * s), "Bold"),
                  fill=LACE, anchor="ls", tracking=int(2 * s), shadow=False)
        # progress bar with the real position in the song
        px0, px1, py = x0 + int(24 * s), x0 + lw - int(24 * s), y0 + lh - int(14 * s)
        frac = min(1.0, t_abs / self.duration)
        d.line((px0, py, px1, py), fill=rgba(SILVER, 70), width=max(1, int(3 * s)))
        d.line((px0, py, px0 + (px1 - px0) * frac, py), fill=rgba(ICE), width=max(1, int(3 * s)))
        kx = px0 + (px1 - px0) * frac
        d.ellipse((kx - 5 * s, py - 5 * s, kx + 5 * s, py + 5 * s), fill=rgba(LACE))
        tm = f"{int(t_abs // 60)}:{int(t_abs % 60):02d} / {int(self.duration // 60)}:{int(self.duration % 60):02d}"
        draw_text(img, (x0 + lw - int(22 * s), y0 + int(38 * s)), tm, font("bahn", int(20 * s), "SemiBold"),
                  fill=SILVER, anchor="rs", shadow=False)

    def frame(self, v, bass, phase, t_abs):
        w, h, s, cx, cy = self.w, self.h, self.s, self.cx, self.cy
        img = self.bg.copy()
        # beat flash
        if bass > 0.55:
            fl = Image.new("RGBA", (w, h), rgba(VIOLET, int(70 * (bass - 0.55) / 0.45)))
            fl.putalpha(Image.new("L", (w, h), 0))
            g = Image.new("L", (w, h), 0)
            rr = self.r * 3.2
            ImageDraw.Draw(g).ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=int(110 * (bass - 0.55) / 0.45))
            fl.putalpha(g.filter(ImageFilter.GaussianBlur(60 * s)))
            img.alpha_composite(fl)
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        # particles drifting upward, looping with `phase`
        P = self.p
        cols = [ICE, LACE, BLUE, LILAC]
        for k in range(len(P["x"])):
            yy = (P["y"][k] - phase * (h + 40) * P["d"][k]) % (h + 40) - 20
            xx = P["x"][k] + 20 * s * math.sin(2 * math.pi * phase * P["d"][k] + P["ph"][k])
            a = int(min(255, 110 + 120 * bass + 40 * math.sin(4 * math.pi * phase + P["ph"][k])))
            c = cols[P["col"][k]]
            if P["star"][k]:
                sparkle(d, xx, yy, int(P["size"][k] * 3), c, a)
            else:
                rr = P["size"][k]
                d.ellipse((xx - rr, yy - rr, xx + rr, yy + rr), fill=rgba(c, a))
        # circular spectrum: low frequencies at the top, mirrored left/right
        n = BANDS * 2
        r0 = self.r * (1.12 + 0.05 * bass)
        bw = max(2, int(7 * s))
        for i in range(n):
            b = i if i < BANDS else n - 1 - i
            val = v[b]
            ang = -math.pi / 2 + (i + 0.5) / n * 2 * math.pi
            ln = (8 + 118 * val) * s
            x0, y0 = cx + math.cos(ang) * r0, cy + math.sin(ang) * r0
            x1, y1 = cx + math.cos(ang) * (r0 + ln), cy + math.sin(ang) * (r0 + ln)
            side = (math.cos(ang) + 1) / 2  # 0 = left, 1 = right
            col = mix(ICE, VIOLET, side)
            if val > 0.82:
                col = mix(col, MAGENTA, (val - 0.82) / 0.18)
            d.line((x0, y0, x1, y1), fill=rgba(col), width=bw)
        # mirrored bar spectrum along the bottom
        nb = 64
        bx0, bx1, base = 80 * s, w - 80 * s, h - 46 * s
        step = (bx1 - bx0) / nb
        for i in range(nb):
            b = int(i / nb * BANDS) if i < nb // 2 else int((nb - 1 - i) / nb * BANDS)
            val = v[b]
            hh = (4 + 46 * val) * s
            x = bx0 + i * step + step * 0.2
            col = mix(ICE, VIOLET, i / nb)
            d.rectangle((x, base - hh, x + step * 0.6, base), fill=rgba(col, 200))
            d.rectangle((x, base + 4 * s, x + step * 0.6, base + 4 * s + hh * 0.4), fill=rgba(col, 60))
        img.alpha_composite(blur_glow(layer, 7 * s, 1.6))
        img.alpha_composite(layer)
        # medallion
        rr = int(self.r * (1 + 0.04 * bass))
        face = self.face.resize((2 * rr, 2 * rr), Image.LANCZOS)
        ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((cx - rr - 6 * s, cy - rr - 6 * s, cx + rr + 6 * s, cy + rr + 6 * s),
                                     outline=rgba(mix(ICE, MAGENTA, max(0, bass - 0.6) / 0.4)), width=max(2, int(6 * s)))
        img.alpha_composite(blur_glow(ring, 10 * s, 1.5 + bass))
        img.alpha_composite(face, (cx - rr, cy - rr))
        img.alpha_composite(ring)
        self.label(img, t_abs)
        if self.overlay is not None:
            img.alpha_composite(self.overlay)
        return img.convert("RGB")


def encode(cmd, frames_iter):
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames_iter:
        proc.stdin.write(f.tobytes())
    proc.stdin.close()
    if proc.wait():
        raise SystemExit("ffmpeg failed")


def loop():
    x = load_audio()
    dur = len(x) / SR
    period, start = tempo_and_start(x)
    beats = max(8, round(12 / period / 8) * 8)  # whole bars (even if the tempo is double-time), ~12 s
    L = beats * period
    N = round(L * FPS)
    K = 12  # crossfade frames
    print(f"tempo {60 / period:.1f} bpm, loop {start:.2f}s + {L:.2f}s ({beats} beats, {N} frames)")
    times = start + (np.arange(-K, N)) / FPS
    v_all = analyse(x, times)
    pre, v = v_all[:K], v_all[K:].copy()
    for j in range(K):  # blend the tail into the frames just before the loop start => seamless
        wgt = (j + 1) / (K + 1)
        v[N - K + j] = v[N - K + j] * (1 - wgt) + pre[j] * wgt
    bass = v[:, :6].mean(axis=1)
    sc = Scene(1440, 620, dur, framed=True)
    out = OUT / "nowplaying.webm"
    encode(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1440x620", "-r", str(FPS),
            "-i", "-", "-vf", "scale=1028:442:flags=lanczos", "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "41",
            "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", "-an", str(out)],
           (sc.frame(v[i], bass[i], i / N, start + i / FPS) for i in range(N)))
    print(f"nowplaying.webm: {out.stat().st_size / 1024:.0f} KB")


def full():
    x = load_audio()
    dur = len(x) / SR
    N = int(dur * FPS)
    times = np.arange(N) / FPS
    v = analyse(x, times)
    bass = v[:, :6].mean(axis=1)
    sc = Scene(1920, 1080, dur)
    exp = ROOT / "export"
    exp.mkdir(exist_ok=True)
    out = exp / "rem-visualizer-full.mp4"
    cyc = 12 * FPS
    encode(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", str(FPS),
            "-i", "-", "-i", str(ROOT / "music.mp3"), "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
            "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(out)],
           (sc.frame(v[i], bass[i], (i % cyc) / cyc, i / FPS) for i in range(N)))
    print(f"{out.name}: {out.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    {"loop": loop, "full": full}[sys.argv[1] if len(sys.argv) > 1 else "loop"]()
