"""Loading the brand style file and timeline files (YAML or JSON) into simple objects."""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .util import AUDIO_EXT, IMAGE_EXT, ROOT, VIDEO_EXT, SFLError, rel, resolve, slugify

# Built-in defaults. config/brand.yaml overrides any of these; a timeline can override
# brand values again with a "style:" section.
DEFAULT_BRAND = {
    "channel": {
        "name": "Smart Finds Lab",
        "tagline": "Discover. Compare. Buy Smarter.",
        "watermark": {"enabled": True, "text": "SMART FINDS LAB", "position": "top-right", "opacity": 0.55},
        "logo": {"file": None, "width": 150, "position": "top-right", "opacity": 0.9},
    },
    "colors": {
        "primary": "#14B8A6",
        "secondary": "#FFB020",
        "dark": "#0B1220",
        "dark2": "#123A4A",
        "light": "#FFFFFF",
        "muted": "#CBD5E1",
    },
    "fonts": {
        "folder": "assets/fonts",
        "heading": {"name": "Inter ExtraBold", "file": "Inter-ExtraBold.otf"},
        "body": {"name": "Inter SemiBold", "file": "Inter-SemiBold.otf"},
        "caption": {"name": "Inter Black", "file": "Inter-Black.otf"},
    },
    "look": {"brightness": 0.0, "contrast": 1.04, "saturation": 1.08, "gamma": 1.0, "sharpen": 0.25, "vignette": False},
    "transitions": {"default": "fade", "duration": 0.5, "video_fade_in": 0.4, "video_fade_out": 1.0},
    "audio": {
        "voice_volume_db": 0.0,
        "voice_cleanup": True,
        "music_volume_db": -19.0,
        "music_fade_in": 1.5,
        "music_fade_out": 3.0,
        "duck_music_under_voice": True,
        "duck_threshold": 0.03,
        "duck_ratio": 6,
        "sfx_volume_db": -8.0,
        "transition_sfx": "assets/sound-effects/generated/whoosh.wav",
        "overlay_sfx": "assets/sound-effects/generated/pop.wav",
        "loudness_lufs": -14.0,
        "true_peak_db": -1.5,
    },
    "formats": {
        "long": {"width": 1920, "height": 1080, "fps": 30, "crf": 18, "preset": "medium", "audio_bitrate": "192k"},
        "short": {"width": 1080, "height": 1920, "fps": 30, "crf": 18, "preset": "medium", "audio_bitrate": "192k"},
    },
    "text_sizes": {
        "long": {"title": 100, "subtitle_line": 44, "lower_third": 50, "lower_third_sub": 32, "badge": 64,
                 "callout": 36, "cta": 34, "card_title": 104, "card_sub": 44, "watermark": 22, "hook": 84,
                 "subtitles": 44},
        "short": {"title": 84, "subtitle_line": 42, "lower_third": 46, "lower_third_sub": 30, "badge": 60,
                  "callout": 36, "cta": 38, "card_title": 88, "card_sub": 42, "watermark": 24, "hook": 70,
                  "subtitles": 76},
    },
    "subtitles": {
        "long": {"font": "body", "color": "#FFFFFF", "box_color": "#000000", "box_opacity": 0.45,
                 "margin_bottom": 56, "max_chars_per_line": 42, "max_lines": 2, "uppercase": False},
        "short": {"font": "caption", "color": "#FFFFFF", "highlight_color": "#FFB020", "outline_color": "#000000",
                  "outline": 7, "position_y": 0.68, "max_words": 3, "max_chars": 18, "uppercase": True,
                  "pop_animation": True},
    },
    "intro": {"enabled": True, "duration": 2.6, "position": "start", "title": None, "subtitle": None,
              "background": "gradient", "sfx": "assets/sound-effects/generated/riser.wav"},
    "outro": {"enabled": True, "duration": 10.0, "title": "Thanks for watching!",
              "subtitle": "Subscribe for more smart finds", "note": "Links & prices: see the description",
              "background": "gradient"},
    "shorts": {"hook_duration": 3.0, "cta_text": "Full review on the channel", "cta_duration": 2.5,
               "fit": "auto", "transition_duration": 0.3, "min_seconds": 20, "max_seconds": 60},
    "images": {"default_duration": 4.0, "motion": "zoom_in", "fit": "cover"},
    "voice": {"delay": 0.15, "tail": 0.45},
}

TRANSITIONS = {"cut", "fade", "fadeblack", "fadewhite", "dissolve", "wipeleft", "wiperight", "wipeup",
               "wipedown", "slideleft", "slideright", "slideup", "slidedown", "smoothleft", "smoothright",
               "smoothup", "smoothdown", "circleopen", "circleclose", "radial", "distance", "pixelize",
               "zoomin", "hblur"}
OVERLAY_TYPES = {"title", "lower_third", "badge", "callout", "text", "cta", "hook"}
FITS = {"cover", "contain", "blur", "auto", "center", "focus"}
MOTIONS = {"none", "zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"}
# graphic cards: a 'card' clip with 'graphic: <kind>' and 'text' (drawn by graphics.py)
GRAPHIC_KINDS = {"pros_cons", "spec", "disclosure", "halfway", "recap", "cta", "note"}


def deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_file(path) -> dict:
    path = resolve(path)
    if not path or not path.exists():
        raise SFLError(f"Config file not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise SFLError(
            f"There is a typing mistake in {rel(path)}.\n{e}\n"
            "Tip: check indentation (use spaces, not tabs) and that text with ':' is in quotes."
        )
    if not isinstance(data, dict):
        raise SFLError(f"{rel(path)} is empty or not a valid timeline.")
    return data


def load_brand(path=None, overrides=None) -> dict:
    brand = copy.deepcopy(DEFAULT_BRAND)
    p = resolve(path or "config/brand.yaml")
    if p.exists():
        brand = deep_merge(brand, load_file(p))
    if overrides:
        brand = deep_merge(brand, overrides)
    return brand


# --------------------------------------------------------------------------- objects
@dataclass
class Clip:
    kind: str                      # video | image | card
    source: Path | None = None
    start: float = 0.0             # trim-in (seconds into the source video)
    end: float | None = None       # trim-out
    duration: float | None = None  # wanted length on the timeline
    fit: str | None = None
    motion: str | None = None
    focus_x: float | None = None   # 0 = left, 0.5 = centre, 1 = right (for cropping)
    focus_y: float | None = None
    speed: float = 1.0
    clip_audio: float = 0.0        # 0 = mute original sound, 1 = full volume
    background: str | None = None  # for cards: gradient | #hex | image path
    zoom: float | None = None      # images: base zoom (1 = whole picture, 1.4 = closer detail crop)
    graphic: str | None = None     # cards: graphic card kind (pros_cons, spec, ...), see GRAPHIC_KINDS
    text: str = ""                 # cards: graphic card text
    raw: dict = field(default_factory=dict)


@dataclass
class Scene:
    id: str
    clips: list
    duration: float | None = None
    voice: Path | None = None
    voice_start: float = 0.0       # trim-in for the voice file
    voice_end: float | None = None
    voice_delay: float | None = None
    voice_volume_db: float = 0.0
    narration: str = ""
    subtitle_file: Path | None = None
    transition: str | None = None  # how this scene STARTS (transition from the previous scene)
    transition_duration: float | None = None
    overlays: list = field(default_factory=list)
    sfx: list = field(default_factory=list)
    look: dict = field(default_factory=dict)
    fill: str = "cycle"            # what to do if clips are shorter than the voice: cycle | freeze | slow
    card: dict | None = None       # title/subtitle for card scenes
    auto: str | None = None        # "intro" / "outro" for generated scenes
    short_fit: str | None = None
    short_focus_x: float | None = None
    # filled in by the planner
    voice_segments: list = field(default_factory=list)  # [(file, src_start, length, offset_in_scene)]
    cue_source: list = field(default_factory=list)      # [(start_in_scene, end_in_scene, text)]


@dataclass
class Project:
    name: str
    title: str
    fmt: str                        # long | short
    brand: dict
    scenes: list
    output: Path
    config_path: Path | None
    audio: dict
    subtitles: dict
    intro: dict
    outro: dict
    hook: dict | None = None        # shorts: opening text
    cta: dict | None = None         # shorts: closing text
    narration: str = ""
    issues: list = field(default_factory=list)   # (level, message) found while reading config

    @property
    def W(self):
        return int(self.brand["formats"][self.fmt]["width"])

    @property
    def H(self):
        return int(self.brand["formats"][self.fmt]["height"])

    @property
    def fps(self):
        return int(self.brand["formats"][self.fmt]["fps"])


def _num(v, name, issues, default=None):
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        issues.append(("error", f"'{name}' must be a number (seconds), got '{v}'"))
        return default


def guess_kind(source) -> str:
    ext = Path(str(source)).suffix.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    return "video"


def parse_clip(d: dict, where: str, issues: list) -> Clip:
    kind = (d.get("type") or "").lower() or (guess_kind(d["source"]) if d.get("source") else "card")
    if kind in ("color", "colour"):
        kind = "card"
    if kind not in ("video", "image", "card"):
        issues.append(("error", f"{where}: unknown type '{kind}' (use video, image or card)"))
        kind = "card"
    if kind in ("video", "image") and not d.get("source"):
        issues.append(("error", f"{where}: a {kind} needs a 'source' file"))
    if kind == "audio":
        issues.append(("error", f"{where}: '{d.get('source')}' is an audio file - put it under 'voice' instead"))
    fit = d.get("fit")
    if fit and fit not in FITS:
        issues.append(("error", f"{where}: fit '{fit}' unknown. Use one of {sorted(FITS)}"))
    motion = d.get("motion")
    if motion and motion not in MOTIONS:
        issues.append(("error", f"{where}: motion '{motion}' unknown. Use one of {sorted(MOTIONS)}"))
    c = Clip(
        kind=kind,
        source=resolve(d.get("source")) if d.get("source") else None,
        start=_num(d.get("start"), f"{where}.start", issues, 0.0),
        end=_num(d.get("end"), f"{where}.end", issues),
        duration=_num(d.get("duration"), f"{where}.duration", issues),
        fit=fit,
        motion=motion,
        focus_x=_num(d.get("focus_x"), f"{where}.focus_x", issues),
        focus_y=_num(d.get("focus_y"), f"{where}.focus_y", issues),
        speed=_num(d.get("speed"), f"{where}.speed", issues, 1.0) or 1.0,
        clip_audio=_num(d.get("clip_audio", d.get("clip_audio_volume")), f"{where}.clip_audio", issues, 0.0),
        background=d.get("background"),
        zoom=_num(d.get("zoom"), f"{where}.zoom", issues),
        graphic=(str(d["graphic"]) if d.get("graphic") else None),
        text=str(d.get("text") or ""),
        raw=d,
    )
    if c.zoom is not None and not (1.0 <= c.zoom <= 2.5):
        issues.append(("error", f"{where}: zoom must be between 1.0 and 2.5"))
        c.zoom = None
    if c.graphic is not None:
        if c.kind != "card":
            issues.append(("error", f"{where}: 'graphic' is only allowed on card clips"))
        elif c.graphic not in GRAPHIC_KINDS:
            issues.append(("error", f"{where}: graphic '{c.graphic}' unknown. Use one of {sorted(GRAPHIC_KINDS)}"))
            c.graphic = None
    if c.end is not None and c.end <= c.start:
        issues.append(("error", f"{where}: end ({c.end}) must be after start ({c.start})"))
    if not (0.25 <= c.speed <= 4):
        issues.append(("error", f"{where}: speed must be between 0.25 and 4"))
    return c


def parse_scene(d: dict, idx: int, issues: list, brand: dict) -> Scene:
    sid = str(d.get("id") or f"scene{idx + 1}")
    where = f"scene '{sid}'"
    if d.get("clips"):
        clips = [parse_clip(c if isinstance(c, dict) else {"source": c}, f"{where} clip {i + 1}", issues)
                 for i, c in enumerate(d["clips"])]
    elif d.get("source") or d.get("type") in ("video", "image"):
        clips = [parse_clip(d, where, issues)]
    else:  # a title card
        clips = [parse_clip({"type": "card", "background": d.get("background")}, where, issues)]
    card = None
    if clips and clips[0].kind == "card" and len(clips) == 1 and not clips[0].graphic:
        card = {"title": d.get("title", ""), "subtitle": d.get("subtitle", "")}
    trans = d.get("transition")
    if trans and str(trans) not in TRANSITIONS:
        issues.append(("error", f"{where}: transition '{trans}' unknown. Use one of: {', '.join(sorted(TRANSITIONS))}"))
        trans = None
    overlays = []
    for i, o in enumerate(d.get("overlays") or []):
        if not isinstance(o, dict) or o.get("type") not in OVERLAY_TYPES:
            issues.append(("error", f"{where} overlay {i + 1}: type must be one of {sorted(OVERLAY_TYPES)}"))
            continue
        overlays.append(o)
    sfx = []
    for i, s in enumerate(d.get("sfx") or []):
        if isinstance(s, str):
            s = {"file": s}
        if not s.get("file"):
            issues.append(("error", f"{where} sfx {i + 1}: needs 'file'"))
            continue
        sfx.append({"file": resolve(s["file"]), "at": float(s.get("at", 0)), "volume_db": float(s.get("volume_db", 0))})
    short = d.get("shorts") or {}
    sc = Scene(
        id=sid,
        clips=clips,
        duration=_num(d.get("duration"), f"{where}.duration", issues),
        voice=resolve(d.get("voice")) if d.get("voice") else None,
        voice_start=_num(d.get("voice_start"), f"{where}.voice_start", issues, 0.0),
        voice_end=_num(d.get("voice_end"), f"{where}.voice_end", issues),
        voice_delay=_num(d.get("voice_delay"), f"{where}.voice_delay", issues),
        voice_volume_db=_num(d.get("voice_volume_db"), f"{where}.voice_volume_db", issues, 0.0),
        narration=str(d.get("narration") or "").strip(),
        subtitle_file=resolve(d.get("subtitles")) if d.get("subtitles") else None,
        transition=trans,
        transition_duration=_num(d.get("transition_duration"), f"{where}.transition_duration", issues),
        overlays=overlays,
        sfx=sfx,
        look=d.get("look") or {},
        fill=d.get("fill", "cycle"),
        card=card,
        short_fit=short.get("fit"),
        short_focus_x=_num(short.get("focus_x"), f"{where}.shorts.focus_x", issues),
    )
    if sc.fill not in ("cycle", "freeze", "slow"):
        issues.append(("error", f"{where}: fill must be cycle, freeze or slow"))
        sc.fill = "cycle"
    return sc


def load_timeline(path, fmt_override: str | None = None) -> Project:
    path = resolve(path)
    raw = load_file(path)
    issues: list = []
    proj = raw.get("project") or {}
    brand = load_brand(raw.get("brand"), raw.get("style"))
    fmt = (fmt_override or proj.get("format") or "long").lower()
    if fmt not in ("long", "short"):
        raise SFLError(f"project.format must be 'long' or 'short' (got '{fmt}')")
    if "fps" in proj:
        brand["formats"][fmt]["fps"] = int(proj["fps"])
    title = proj.get("title") or path.stem
    name = slugify(proj.get("output") or path.stem)
    scenes_raw = raw.get("scenes") or []
    if not scenes_raw:
        raise SFLError(f"{rel(path)} has no 'scenes:' list. Add at least one scene.")
    scenes = [parse_scene(s, i, issues, brand) for i, s in enumerate(scenes_raw)]
    ids = [s.id for s in scenes]
    for d in {i for i in ids if ids.count(i) > 1}:
        issues.append(("error", f"scene id '{d}' is used more than once - ids must be unique"))
    folder = "long-videos" if fmt == "long" else "shorts"
    out = ROOT / "output" / folder / f"{name}.mp4"
    intro = deep_merge(brand["intro"], raw.get("intro") or {}) if fmt == "long" else {"enabled": False}
    outro = deep_merge(brand["outro"], raw.get("outro") or {}) if fmt == "long" else {"enabled": False}
    audio = raw.get("audio") or {}
    for k in ("voiceover", "music"):
        if audio.get(k):
            audio[k] = resolve(audio[k])
    subs = raw.get("subtitles") or {}
    subs.setdefault("mode", "auto")
    subs.setdefault("burn_in", True)
    subs.setdefault("export_srt", True)
    if subs.get("file"):
        subs["file"] = resolve(subs["file"])
    return Project(
        name=name, title=title, fmt=fmt, brand=brand, scenes=scenes, output=out, config_path=path,
        audio=audio, subtitles=subs, intro=intro, outro=outro,
        hook=raw.get("hook"), cta=raw.get("cta"), narration=str(raw.get("narration") or ""), issues=issues,
    )
