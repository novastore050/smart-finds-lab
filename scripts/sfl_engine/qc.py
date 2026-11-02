"""Quality control: checks before rendering (pre-flight) and after exporting, plus reports."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .plan import Plan
from .util import SFLError, probe, rel, resolve, run_ffmpeg_analysis

OK, INFO, WARN, ERR = "ok", "info", "warning", "error"
ICON = {OK: "✅", INFO: "ℹ️", WARN: "⚠️", ERR: "❌"}

# Phrases that would claim hands-on testing. The channel researches products; it must not
# say it physically tested them unless that is true.
CLAIM_PATTERNS = [r"\bI (?:have |'ve )?tested\b", r"\bwe (?:have |'ve )?tested\b", r"\bafter testing\b",
                  r"\bin my testing\b", r"\bI(?:'ve| have) been using\b", r"\bhands[- ]on\b", r"\bI bought\b",
                  r"\bwe bought\b", r"\bour tests?\b", r"\bmy tests?\b"]
PLACEHOLDER = re.compile(r"\[[^\]]*\]|\bTODO\b|\bXXX\b|PRODUCT[_ ]?\d+[_ ]NAME", re.I)


class Checks:
    def __init__(self):
        self.items = []

    def add(self, level, area, msg):
        if any(i["area"] == area and i["message"] == msg for i in self.items):
            return  # same message once only
        self.items.append({"level": level, "area": area, "message": msg})

    def count(self, level):
        return sum(1 for i in self.items if i["level"] == level)

    @property
    def status(self):
        if self.count(ERR):
            return "FAIL"
        return "PASS WITH WARNINGS" if self.count(WARN) else "PASS"


# --------------------------------------------------------------------------- pre-flight
def preflight(plan: Plan, checks: Checks | None = None) -> Checks:
    ck = checks or Checks()
    proj = plan.project
    for lvl, msg in proj.issues:
        ck.add(ERR if lvl == "error" else WARN, "Timeline file", msg)
    for e in plan.errors:
        ck.add(ERR, "Media files", e)

    # ---- media files
    seen = set()
    n_missing = 0
    for ps in plan.scenes:
        sc = ps.scene
        for c in sc.clips:
            if not c.source or c.source in seen:
                continue
            seen.add(c.source)
            if not c.source.exists():
                n_missing += 1
                continue  # already reported by the planner
            try:
                info = probe(c.source)
            except SFLError as e:
                ck.add(ERR, "Media files", str(e))
                continue
            if c.kind == "video":
                if not info["has_video"]:
                    ck.add(ERR, "Media files", f"{rel(c.source)} has no video picture")
                    continue
                dur = info["duration"] or 0
                if c.end and c.end > dur + 0.05:
                    ck.add(WARN, "Trimming", f"{rel(c.source)}: end={c.end}s but the clip is only {dur:.2f}s "
                                             "- it will stop at the real end")
                short_side = min(info["width"], info["height"])
                if short_side < 720:
                    ck.add(WARN, "Quality", f"{rel(c.source)} is low resolution ({info['width']}x{info['height']})")
                if info["fps"] and info["fps"] < 23:
                    ck.add(WARN, "Quality", f"{rel(c.source)} has a low frame rate ({info['fps']:.1f} fps)")
            ar = info["width"] / info["height"] if info.get("width") else None
            if ar and abs(ar / (plan.W / plan.H) - 1) > 0.2:
                ck.add(INFO, "Aspect ratio", f"{rel(c.source)} is {info['width']}x{info['height']} - it will be "
                                             f"reframed to {plan.W}x{plan.H} (fit: {c.fit or 'auto'})")
            if c.kind == "image" and info.get("width") and max(info["width"], info["height"]) < 1000:
                ck.add(WARN, "Quality", f"{rel(c.source)} is small ({info['width']}x{info['height']}) - may look blurry")
    for v in plan.voices:
        try:
            info = probe(v["file"])
            if not info["has_audio"]:
                ck.add(ERR, "Audio", f"{rel(v['file'])} has no sound")
        except SFLError as e:
            ck.add(ERR, "Audio", str(e))
    music = proj.audio.get("music")
    if music:
        if not music.exists():
            ck.add(ERR, "Audio", f"music file not found: {rel(music)}")
        if not proj.audio.get("music_license"):
            ck.add(WARN, "Copyright", "No 'music_license' written for the background music. Note where it comes "
                                      "from (e.g. 'YouTube Audio Library - no attribution required').")
    else:
        ck.add(INFO, "Audio", "no background music set")
    if not plan.voices:
        ck.add(WARN, "Audio", "no voice-over in this video")
    for s in plan.sfx:
        f = resolve(s["file"])
        if f and not f.exists():
            ck.add(INFO if s.get("auto") else WARN, "Sound effects",
                   f"sound effect not found: {rel(f)}" + (" (run: python scripts/sfl.py make-sfx)" if s.get("auto") else ""))
    logo = (proj.brand["channel"].get("logo") or {}).get("file")
    if logo and not resolve(logo).exists():
        ck.add(ERR, "Branding", f"logo file not found: {logo}")

    # ---- text content
    texts = []
    for ps in plan.scenes:
        sc = ps.scene
        texts.append((f"scene '{sc.id}' narration", sc.narration))
        for o in sc.overlays:
            texts.append((f"scene '{sc.id}' {o['type']}", f"{o.get('text', '')} {o.get('subtitle', '')}"))
        if sc.card:
            texts.append((f"scene '{sc.id}' card", f"{sc.card.get('title', '')} {sc.card.get('subtitle', '')}"))
    if proj.hook:
        texts.append(("hook", str(proj.hook.get("text", "") if isinstance(proj.hook, dict) else proj.hook)))
    texts.append(("narration", proj.narration))
    for a, b, t in plan.cues:
        texts.append(("subtitles", t))
    for where, t in texts:
        if not t:
            continue
        if PLACEHOLDER.search(t):
            ck.add(WARN, "Placeholder text", f"{where} still contains placeholder text: \"{t.strip()[:70]}\"")
        for pat in CLAIM_PATTERNS:
            if re.search(pat, t, re.I):
                ck.add(WARN, "Honesty", f"{where} says \"{re.search(pat, t, re.I).group(0)}\" - only claim testing "
                                        "if you really tested the product. Prefer 'based on specs and reviews'.")
                break

    # ---- subtitles
    _check_cues(plan, ck)

    # ---- timing / duration
    for w in plan.warnings:
        ck.add(WARN, "Timeline", w)
    if proj.fmt == "short":
        lo, hi = float(proj.brand["shorts"]["min_seconds"]), float(proj.brand["shorts"]["max_seconds"])
        if plan.total > 180:
            ck.add(ERR, "Duration", f"Short is {plan.total:.1f}s - YouTube Shorts must be 3 minutes or less")
        elif not lo <= plan.total <= hi:
            ck.add(WARN, "Duration", f"Short is {plan.total:.1f}s - your target range is {lo:.0f}-{hi:.0f}s")
        else:
            ck.add(OK, "Duration", f"Short length {plan.total:.1f}s is inside {lo:.0f}-{hi:.0f}s")
    else:
        ck.add(OK if plan.total >= 60 else INFO, "Duration", f"planned length {fmt_time(plan.total)}")
    if not ck.count(ERR):
        ck.add(OK, "Media files", f"all {len(seen)} clip/image files found and readable")
    return ck


def _check_cues(plan: Plan, ck: Checks):
    cues = plan.cues
    if not cues:
        if str(plan.project.subtitles.get("mode")) not in ("none", "off"):
            ck.add(WARN, "Subtitles", "no subtitles - add 'narration' text, an .srt file, or install Whisper")
        return
    bad_overlap = sum(1 for (a1, b1, _), (a2, b2, _) in zip(cues, cues[1:]) if a2 < b1 - 0.05)
    too_short = [c for c in cues if c[1] - c[0] < 0.6]
    too_fast = [c for c in cues if len(c[2]) / max(0.1, c[1] - c[0]) > 22]
    if bad_overlap:
        ck.add(WARN, "Subtitles", f"{bad_overlap} subtitle(s) overlap the next one")
    if too_short:
        ck.add(WARN, "Subtitles", f"{len(too_short)} subtitle(s) shown for under 0.6s (hard to read)")
    if too_fast:
        ck.add(WARN, "Subtitles", f"{len(too_fast)} subtitle(s) need fast reading (> 22 characters/second)")
    if cues[-1][1] > plan.total + 0.05:
        ck.add(WARN, "Subtitles", "subtitles continue after the end of the video")
    methods = sorted(set(plan.cue_method.values()))
    est = any("estimated" in m for m in methods)
    ck.add(OK if not est else INFO, "Subtitles",
           f"{len(cues)} subtitles; source: {', '.join(methods) or 'n/a'}"
           + (" - timing is estimated from the script; check it, or use an .srt / Whisper for exact sync" if est else ""))


# --------------------------------------------------------------------------- post-export
def postcheck(out: Path, plan: Plan, log, checks: Checks, srt: Path | None = None) -> dict:
    proj = plan.project
    fmt = proj.brand["formats"][proj.fmt]
    stats = {}
    try:
        info = probe(out)
    except SFLError as e:
        checks.add(ERR, "Export", f"exported file cannot be read: {e}")
        return stats
    stats.update(info)
    W, H = int(fmt["width"]), int(fmt["height"])
    checks.add(OK if (info["width"], info["height"]) == (W, H) else ERR, "Resolution",
               f"{info['width']}x{info['height']} (expected {W}x{H}, "
               f"{'16:9' if proj.fmt == 'long' else '9:16'})")
    checks.add(OK if info["vcodec"] == "h264" and info["pix_fmt"] == "yuv420p" else ERR, "Codec",
               f"video {info['vcodec']} {info['pix_fmt']}, audio {info['acodec']} {info['sample_rate']} Hz")
    if info["acodec"] != "aac":
        checks.add(ERR, "Codec", "audio is not AAC")
    if info["fps"] and abs(info["fps"] - plan.fps) > 0.01:
        checks.add(ERR, "Frame rate", f"{info['fps']:.3f} fps, expected {plan.fps}")
    else:
        checks.add(OK, "Frame rate", f"{plan.fps} fps")
    vd, ad = info.get("video_duration") or info["duration"], info.get("audio_duration") or info["duration"]
    diff = abs(vd - plan.total)
    checks.add(OK if diff < 0.1 else WARN, "Duration", f"final video {fmt_time(vd)} (planned {fmt_time(plan.total)})")
    if ad is not None:
        checks.add(OK if abs(ad - vd) < 0.15 else WARN, "Audio sync",
                   f"audio track {ad:.2f}s vs video {vd:.2f}s (difference {abs(ad - vd) * 1000:.0f} ms)")
    late = [v for v in plan.voices if v["at"] + v["length"] > plan.total + 0.05]
    if late:
        checks.add(WARN, "Audio sync", f"{len(late)} voice clip(s) run past the end of the video and are cut off")
    else:
        checks.add(OK, "Audio sync", f"{len(plan.voices)} voice clip(s) placed inside their scenes")

    # ---- one decoding pass: black frames, silence, loudness
    err = run_ffmpeg_analysis(["-i", str(out), "-vf", "blackdetect=d=0.5:pix_th=0.08",
                               "-af", "silencedetect=n=-50dB:d=3,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                               "-f", "null", "-"], log, "analysing final video")
    fade_in = float(proj.brand["transitions"].get("video_fade_in", 0)) + 0.3
    fade_out = plan.total - float(proj.brand["transitions"].get("video_fade_out", 0)) - 0.3
    blacks = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    blacks = [(a, b) for a, b in blacks if not (b <= fade_in or a >= fade_out)]
    if blacks:
        checks.add(WARN, "Black frames", "black picture at " + ", ".join(f"{fmt_time(a)}-{fmt_time(b)}" for a, b in blacks[:8]))
    else:
        checks.add(OK, "Black frames", "no unexpected black sections found")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)] + [plan.total]
    silences = [(max(0, a), b) for a, b in zip(starts, ends) if b - a >= 3]
    if silences:
        checks.add(WARN if proj.audio.get("music") else INFO, "Silence",
                   "silent audio at " + ", ".join(f"{fmt_time(a)}-{fmt_time(b)}" for a, b in silences[:8]))
    else:
        checks.add(OK, "Silence", "no long silent gaps")
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S)
    if m:
        ln = json.loads(m.group(0))
        stats["lufs"], stats["true_peak"] = ln["input_i"], ln["input_tp"]
        target = float(proj.brand["audio"]["loudness_lufs"])
        try:
            ok = abs(float(ln["input_i"]) - target) <= 1.5
            checks.add(OK if ok else WARN, "Loudness", f"{ln['input_i']} LUFS (target {target}), "
                                                       f"true peak {ln['input_tp']} dBTP")
        except ValueError:
            checks.add(WARN, "Loudness", "audio is silent")
    if srt:
        checks.add(OK if srt.exists() else WARN, "Subtitles", f"SRT for YouTube upload: {rel(srt)}")
    checks.add(OK, "Export", f"{rel(out)} ({out.stat().st_size / 1e6:.1f} MB)")
    return stats


# --------------------------------------------------------------------------- report
def fmt_time(t):
    if t is None:
        return "?"
    m, s = divmod(float(t), 60)
    return f"{int(m)}:{s:05.2f}"


def write_report(path: Path, plan: Plan, checks: Checks, out: Path | None, stats: dict, seconds: float):
    proj = plan.project
    lines = [f"# Quality-control report — {proj.title}", "",
             f"**Status: {checks.status}**  ", f"Created: {time.strftime('%Y-%m-%d %H:%M')}  ",
             f"Timeline: `{rel(proj.config_path)}`  ", f"Output: `{rel(out) if out else '(not rendered)'}`  ",
             f"Format: {proj.fmt} ({plan.W}x{plan.H}, {plan.fps} fps)  ", f"Length: {fmt_time(plan.total)}  "]
    if seconds:
        lines.append(f"Render time: {seconds:.0f} s  ")
    lines += ["", f"Errors: {checks.count(ERR)} · Warnings: {checks.count(WARN)} · Passed: {checks.count(OK)}", "",
              "## Checks", "", "| | Area | Result |", "|---|---|---|"]
    order = {ERR: 0, WARN: 1, INFO: 2, OK: 3}
    for it in sorted(checks.items, key=lambda i: order[i["level"]]):
        lines.append(f"| {ICON[it['level']]} | {it['area']} | {it['message'].replace('|', '/')} |")
    lines += ["", "## Scenes", "", "| # | Scene | Starts | Length | Clips used | Voice | Subtitles |", "|---|---|---|---|---|---|---|"]
    for ps in plan.scenes:
        sc = ps.scene
        clips = ", ".join(sorted({(rel(s.clip.source).split('/')[-1] if s.clip.source else 'title card') for s in ps.segments}))
        voice = rel(sc.voice).split("/")[-1] if sc.voice else ("master voice-over" if proj.audio.get("voiceover") else "—")
        reframe = "; ".join(sorted({getattr(s, "auto_info", "") for s in ps.segments} - {""}))
        if reframe:
            clips += f" *(auto: {reframe})*"
        lines.append(f"| {ps.index + 1} | {sc.id} | {fmt_time(ps.start_f / plan.fps)} | {ps.frames / plan.fps:.1f}s | "
                     f"{clips} | {voice} | {plan.cue_method.get(sc.id, '—')} |")
    lines += ["", "## Before you upload", "",
              "- Watch the whole video once at normal speed (automated checks cannot judge content).",
              "- Check product names, claims and any numbers on screen are correct.",
              "- Upload the `.srt` file as captions in YouTube Studio (better than auto-captions).",
              "- Add your affiliate disclosure in the description (e.g. *As an Amazon Associate I earn from "
              "qualifying purchases*), and tick 'paid promotion' if a brand paid you.",
              "- Add end-screen elements over the outro in YouTube Studio." if proj.fmt == "long" else
              "- Shorts: make sure nothing important sits under YouTube's buttons (right side / bottom)."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    jpath = path.with_suffix(".json")
    jpath.write_text(json.dumps({"status": checks.status, "title": proj.title, "output": str(out) if out else None,
                                 "duration": plan.total, "checks": checks.items,
                                 "stats": {k: v for k, v in stats.items() if isinstance(v, (int, float, str, bool, type(None)))}},
                                indent=2), encoding="utf-8")
    return path
