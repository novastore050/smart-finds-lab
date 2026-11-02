"""Automatic reframing (e.g. 16:9 footage -> 9:16 Shorts).

How 'auto' works (simple and predictable, no AI download needed):
  1. Sample ~10 small grey frames from the clip.
  2. Measure where the picture has detail (edges) and, weighted most, movement (hands, product).
  3. Slide a crop window of the target shape across the frame and pick the position
     that keeps the most detail, with a gentle preference for the centre.
  4. If even the best crop keeps less than ~50 % of the detail (the subject is spread
     wide), use 'blur' instead: the whole frame is shown on a blurred background,
     so nothing important is cut off.
The crop is fixed for the whole clip (no shaky camera).
"""
from __future__ import annotations

import subprocess

import numpy as np

from .util import find_tool, probe

_cache: dict = {}


def analyze(path, start: float, length: float, out_w: int, out_h: int):
    """Return (fit, focus_x, focus_y, coverage) for a video clip."""
    info = probe(path)
    sw, sh = info["width"], info["height"]
    if not sw or not sh:
        return "cover", 0.5, 0.5, 1.0
    out_ar, src_ar = out_w / out_h, sw / sh
    if 0.8 <= src_ar / out_ar <= 1.25:
        return "cover", 0.5, 0.5, 1.0
    key = (str(path), round(start, 2), round(length, 2), out_w, out_h, path.stat().st_mtime)
    if key in _cache:
        return _cache[key]
    horizontal = src_ar > out_ar  # crop window slides left-right
    sw_small = 192
    sh_small = max(2, int(round(sw_small * sh / sw / 2)) * 2)
    n = 10
    rate = max(0.2, n / max(length, 0.5))
    cmd = [find_tool("ffmpeg"), "-v", "error", "-ss", f"{start:.3f}", "-t", f"{max(length, 0.5):.3f}",
           "-i", str(path), "-vf", f"fps={rate:.4f},scale={sw_small}:{sh_small},format=gray",
           "-frames:v", str(n), "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    fsz = sw_small * sh_small
    k = len(raw) // fsz
    if k == 0:
        return "blur", 0.5, 0.5, 0.0
    frames = np.frombuffer(raw[: k * fsz], dtype=np.uint8).reshape(k, sh_small, sw_small).astype(np.float32)
    gx = np.abs(np.diff(frames, axis=2, prepend=frames[:, :, :1]))
    gy = np.abs(np.diff(frames, axis=1, prepend=frames[:, :1, :]))
    energy = (gx + gy).mean(axis=0)
    if k > 1:
        energy += 4.0 * np.abs(np.diff(frames, axis=0)).mean(axis=0)  # movement (hands, product) counts most
    profile = energy.mean(axis=0) if horizontal else energy.mean(axis=1)
    L = len(profile)
    win = int(round((sh_small * out_ar) if horizontal else (sw_small / out_ar)))
    win = max(1, min(L, win))
    if win >= L:
        return "cover", 0.5, 0.5, 1.0
    csum = np.concatenate([[0], np.cumsum(profile)])
    scores = csum[win:] - csum[:-win]
    pos = np.arange(len(scores)) / max(1, len(scores) - 1)
    prior = np.exp(-((pos - 0.5) ** 2) / (2 * 0.35 ** 2))
    best = int(np.argmax(scores * (0.85 + 0.15 * prior)))
    coverage = float(scores[best] / max(csum[-1], 1e-6))
    focus = best / max(1, len(scores) - 1)
    # share of detail that "should" be in the window if spread evenly = win/L
    if coverage < max(0.5, win / L * 1.25):
        result = ("blur", 0.5, 0.5, coverage)
    else:
        result = ("cover", focus if horizontal else 0.5, 0.5 if horizontal else focus, coverage)
    _cache[key] = result
    return result
