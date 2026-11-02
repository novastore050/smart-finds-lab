"""Shared helpers: paths, logging, running FFmpeg/FFprobe, probing media files."""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Project root = the "Smart-Finds-Lab" folder (two levels above this file).
ROOT = Path(__file__).resolve().parents[2]

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


class SFLError(Exception):
    """A friendly, expected error (missing file, bad config, FFmpeg failure)."""


# --------------------------------------------------------------------------- tools
def find_tool(name: str) -> str:
    env = os.environ.get(f"SFL_{name.upper()}")
    if env and Path(env).exists():
        return env
    path = shutil.which(name)
    if not path:
        raise SFLError(
            f"'{name}' was not found. Install FFmpeg and make sure '{name}' works in a terminal.\n"
            "See docs/INSTALL.md (section 'FFmpeg')."
        )
    return path


# --------------------------------------------------------------------------- logging
class Log:
    """Prints short messages to the screen and writes full details to logs/."""

    def __init__(self, name: str):
        (ROOT / "logs").mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.path = ROOT / "logs" / f"{slugify(name)}_{stamp}.log"
        self._f = open(self.path, "w", encoding="utf-8")
        self.debug(f"Smart Finds Lab log - {time.ctime()}")

    def info(self, msg: str = ""):
        print(msg, flush=True)
        self.debug(msg)

    def warn(self, msg: str):
        self.info(f"  WARNING: {msg}")

    def debug(self, msg: str):
        self._f.write(msg + "\n")
        self._f.flush()

    def close(self):
        self._f.close()


# --------------------------------------------------------------------------- ffmpeg
def _fmt_cmd(cmd):
    return " ".join(shlex.quote(str(c)) for c in cmd)


def run_ffmpeg(args, log: Log | None = None, desc: str = "", cwd=None, total: float | None = None):
    """Run ffmpeg with args. Shows a % progress line when total (seconds) is given."""
    cmd = [find_tool("ffmpeg"), "-hide_banner", "-nostdin", "-y", "-loglevel", "error"]
    if total:
        cmd += ["-progress", "pipe:1", "-nostats"]
    cmd += [str(a) for a in args]
    if log:
        log.debug(f"\n[{desc}] $ {_fmt_cmd(cmd)}")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as errf:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE if total else subprocess.DEVNULL,
            stderr=errf,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        last_pct = -1
        if total:
            for line in proc.stdout:
                if line.startswith("out_time="):
                    t = _parse_clock(line.split("=", 1)[1].strip())
                    if t is not None:
                        pct = max(0, min(100, int(t / total * 100)))
                        if pct != last_pct:
                            sys.stdout.write(f"\r    {desc}: {pct:3d}%")
                            sys.stdout.flush()
                            last_pct = pct
            sys.stdout.write("\r" + " " * 60 + "\r")
        rc = proc.wait()
        errf.seek(0)
        err = errf.read()
    if err and log:
        log.debug(err)
    if rc != 0:
        raise SFLError(f"FFmpeg failed while: {desc}\n--- FFmpeg said ---\n{err.strip()[-2500:]}")
    return err


def run_ffmpeg_analysis(args, log: Log | None = None, desc: str = "") -> str:
    """Run ffmpeg for analysis filters (blackdetect, ebur128...) and return its stderr text."""
    cmd = [find_tool("ffmpeg"), "-hide_banner", "-nostdin", "-loglevel", "info"] + [str(a) for a in args]
    if log:
        log.debug(f"\n[{desc}] $ {_fmt_cmd(cmd)}")
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise SFLError(f"FFmpeg analysis failed: {desc}\n{p.stderr[-1500:]}")
    return p.stderr


def _parse_clock(s: str):
    m = re.match(r"(-?\d+):(\d+):(\d+(?:\.\d+)?)", s)
    if not m:
        return None
    h, mi, se = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(se)


# --------------------------------------------------------------------------- probe
_probe_cache: dict = {}


def probe(path) -> dict:
    """Return basic info about a media file. Raises SFLError if unreadable."""
    path = Path(path)
    if not path.exists():
        raise SFLError(f"File not found: {rel(path)}")
    key = (str(path), path.stat().st_mtime, path.stat().st_size)
    if key in _probe_cache:
        return _probe_cache[key]
    cmd = [find_tool("ffprobe"), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise SFLError(f"Cannot read media file (damaged or unsupported): {rel(path)}\n{p.stderr.strip()[:500]}")
    data = json.loads(p.stdout or "{}")
    info = {
        "path": str(path),
        "duration": None,
        "has_video": False,
        "has_audio": False,
        "width": None,
        "height": None,
        "fps": None,
        "vcodec": None,
        "acodec": None,
        "pix_fmt": None,
        "sample_rate": None,
        "channels": None,
        "rotation": 0,
        "is_image": path.suffix.lower() in IMAGE_EXT,
        "video_duration": None,
        "audio_duration": None,
    }
    fmt = data.get("format", {})
    if fmt.get("duration") not in (None, "N/A"):
        info["duration"] = float(fmt["duration"])
    for s in data.get("streams", []):
        if s.get("codec_type") == "video" and not info["has_video"]:
            if s.get("disposition", {}).get("attached_pic"):
                continue  # album cover inside an mp3
            info["has_video"] = True
            info["width"], info["height"] = s.get("width"), s.get("height")
            info["vcodec"] = s.get("codec_name")
            info["pix_fmt"] = s.get("pix_fmt")
            info["fps"] = _fps(s.get("avg_frame_rate")) or _fps(s.get("r_frame_rate"))
            if s.get("duration") not in (None, "N/A"):
                info["video_duration"] = float(s["duration"])
            rot = 0
            for sd in s.get("side_data_list", []) or []:
                if "rotation" in sd:
                    rot = int(float(sd["rotation"]))
            if "rotate" in (s.get("tags") or {}):
                rot = int(s["tags"]["rotate"])
            info["rotation"] = rot
            if abs(rot) % 180 == 90 and info["width"]:
                info["width"], info["height"] = info["height"], info["width"]
        elif s.get("codec_type") == "audio" and not info["has_audio"]:
            info["has_audio"] = True
            info["acodec"] = s.get("codec_name")
            info["sample_rate"] = int(s.get("sample_rate") or 0) or None
            info["channels"] = s.get("channels")
            if s.get("duration") not in (None, "N/A"):
                info["audio_duration"] = float(s["duration"])
    if info["is_image"]:
        info["duration"] = None
    _probe_cache[key] = info
    return info


def _fps(r):
    if not r or r in ("0/0", "N/A"):
        return None
    try:
        a, b = r.split("/")
        return float(a) / float(b) if float(b) else None
    except ValueError:
        return float(r)


# --------------------------------------------------------------------------- misc
def rel(path) -> str:
    """Path shown relative to the project folder (shorter, beginner friendly)."""
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve(path) -> Path | None:
    if path in (None, ""):
        return None
    p = Path(str(path)).expanduser()
    return p if p.is_absolute() else (ROOT / p)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(text)).strip("-").lower()
    return s or "video"


def unique_output(path: Path, overwrite: bool = False) -> Path:
    """Never overwrite an existing export unless asked: add _v2, _v3, ..."""
    if overwrite or not path.exists():
        return path
    n = 2
    while True:
        cand = path.with_name(f"{path.stem}_v{n}{path.suffix}")
        if not cand.exists():
            return cand
        n += 1


def hex_rgb(h: str):
    h = str(h).strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise SFLError(f"Invalid colour '{h}'. Use hex like #00C2A8")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def ass_color(h: str, alpha: float = 0.0) -> str:
    """'#RRGGBB' + transparency (0=opaque, 1=invisible) -> ASS '&HAABBGGRR'."""
    r, g, b = hex_rgb(h)
    a = int(round(max(0.0, min(1.0, alpha)) * 255))
    return f"&H{a:02X}{b:02X}{g:02X}{r:02X}"


def ass_color_tag(h: str) -> str:
    r, g, b = hex_rgb(h)
    return f"&H{b:02X}{g:02X}{r:02X}&"


def ffmpeg_color(h: str) -> str:
    r, g, b = hex_rgb(h)
    return f"0x{r:02X}{g:02X}{b:02X}"


def ffpath(p) -> str:
    """Path for use *inside* an FFmpeg filter argument (forward slashes, escaped)."""
    s = str(p).replace("\\", "/")
    return s.replace(":", "\\:").replace("'", "\\'")
