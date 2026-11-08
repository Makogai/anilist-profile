"""Bring still illustrations to life without new drawings: smooth displacement fields (cv2.remap)
sway hair / ribbons / flowers, rotate a waving hand around the wrist, and blend a closed-eye
version of the art over the eyes for a blink.
"""
import math

import cv2
import numpy as np
from PIL import Image


def hsv_mask(rgb: np.ndarray, hue, s_min=0.35, v_min=0.35, blur=9) -> np.ndarray:
    """Soft 0..1 mask of pixels whose hue (degrees) lies in `hue` (lo, hi); hi < lo wraps around 360."""
    hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
    lo, hi = hue
    inside = (h >= lo) & (h <= hi) if lo <= hi else (h >= lo) | (h <= hi)
    m = (inside & (s >= s_min) & (v >= v_min)).astype(np.float32)
    if blur:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    return np.clip(m * 1.4, 0, 1)


def ellipse_mask(shape, centre, axes, blur):
    m = np.zeros(shape[:2], np.float32)
    cv2.ellipse(m, (int(centre[0]), int(centre[1])), (int(axes[0]), int(axes[1])), 0, 0, 360, 1.0, -1)
    return cv2.GaussianBlur(m, (0, 0), blur)


class Animator:
    """Accumulates displacement for one frame, then samples the source once."""

    def __init__(self, rgba: np.ndarray):
        self.src = rgba
        h, w = rgba.shape[:2]
        self.xx, self.yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        self.reset()

    def reset(self):
        self.mx, self.my = self.xx.copy(), self.yy.copy()

    def sway(self, mask, phase, amp, wavelength=180.0, vertical=0.3, along=(1 / 3, 1.0)):
        """Wind-like ripple through the masked area (phase in cycles). `along` weights how fast the
        wave travels in x and y: the default runs down hair, (1, 0) runs across a field."""
        a = 2 * math.pi * (phase - (self.xx * along[0] + self.yy * along[1]) / wavelength)
        self.mx += amp * mask * np.sin(a)
        self.my += amp * vertical * mask * np.cos(a)

    def rotate(self, mask, pivot, degrees):
        """Rotate the masked area about pivot (mask fades the rotation out toward its edges)."""
        th = np.radians(degrees) * mask
        dx, dy = self.mx - pivot[0], self.my - pivot[1]
        c, s = np.cos(-th), np.sin(-th)
        self.mx, self.my = pivot[0] + c * dx - s * dy, pivot[1] + s * dx + c * dy

    def render(self) -> np.ndarray:
        # numpy scalars (np.radians etc.) promote the maps to float64; remap needs float32
        out = cv2.remap(self.src, self.mx.astype(np.float32), self.my.astype(np.float32), cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT)
        self.reset()
        return out


def blink_amount(t, at=0.55, dur=0.06):
    """0 -> 1 -> 0 around loop phase `at` (smooth, ~dur of the loop)."""
    d = abs(((t - at + 0.5) % 1) - 0.5)
    return max(0.0, 1 - d / (dur / 2)) ** 0.8


def blend_eyes(frame: np.ndarray, closed: np.ndarray, eye_mask: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0:
        return frame
    a = (eye_mask * amount)[..., None]
    out = frame.astype(np.float32) * (1 - a) + closed.astype(np.float32) * a
    return out.astype(np.uint8)


def locate_change(a: np.ndarray, b: np.ndarray, blur=6, thresh=0.35):
    """Bounding box of the region where two near-identical images differ most (e.g. the eyes)."""
    d = np.abs(a[..., :3].astype(np.float32) - b[..., :3].astype(np.float32)).mean(axis=2)
    d = cv2.GaussianBlur(d, (0, 0), blur)
    ys, xs = np.where(d > d.max() * thresh)
    return xs.min(), ys.min(), xs.max(), ys.max(), float(np.median(d)), float(d.max())


def to_np(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGBA")).copy()


def to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(arr, "RGBA")
