"""Timeline planner: turns a Project into exact frame-accurate segments and timed events.

Nothing is rendered here - this only measures files and does arithmetic, so it is fast and
is also used by 'check' (pre-flight quality control).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from .config import Clip, Project, Scene
from .subtitles import (parse_subtitle_file, script_to_cues, whisper_available, whisper_cues)
from .util import SFLError, probe, rel


@dataclass
class Segment:
    clip: Clip
    src_start: float          # seconds into the source file
    frames: int               # frames on the timeline
    src_frames: int           # frames actually taken from the source (rest = frozen last frame)
    speed: float
    scene_id: str
    fit: str = "cover"
    focus_x: float = 0.5
    focus_y: float = 0.5
    look: dict = field(default_factory=dict)
    card_bg: str | None = None
    key: str = ""
    avail: int = 10**9        # source frames available after the trim-in point
    auto_info: str = ""       # what auto-reframe decided (for the QC report)


@dataclass
class PlannedScene:
    scene: Scene
    index: int
    frames: int
    start_f: int              # first frame on the final timeline (including incoming transition)
    trans: str                # transition INTO this scene ("cut" for the first)
    trans_f: int              # transition length in frames
    segments: list


@dataclass
class Plan:
    project: Project
    fps: int
    W: int
    H: int
    scenes: list
    total_frames: int
    voices: list = field(default_factory=list)    # dict(file, src_start, length, at, volume_db, scene)
    sfx: list = field(default_factory=list)       # dict(file, at, volume_db)
    overlays: list = field(default_factory=list)  # dict(type, t0, t1, data, scene)
    cues: list = field(default_factory=list)      # (t0, t1, text)
    cue_method: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def total(self):
        return self.total_frames / self.fps

    def scene_window(self, sid, own=False):
        """(start, end) of a scene in seconds. own=True starts after the incoming transition,
        so windows of neighbouring scenes do not overlap."""
        for ps in self.scenes:
            if ps.scene.id == sid:
                a = ps.start_f + (ps.trans_f if own else 0)
                return a / self.fps, (ps.start_f + ps.frames) / self.fps
        return None


OVERLAY_DEFAULT_DUR = {"title": 3.2, "lower_third": 4.5, "callout": 3.0, "text": 3.0, "cta": 4.0, "hook": 3.0}


def _media_len(path, start=0.0, end=None, want_audio=False):
    info = probe(path)
    if want_audio and not info["has_audio"]:
        raise SFLError(f"{rel(path)} has no audio track")
    dur = info["audio_duration"] if want_audio and info["audio_duration"] else info["duration"]
    if dur is None:
        raise SFLError(f"Cannot find the length of {rel(path)}")
    stop = min(end, dur) if end is not None else dur
    return max(0.0, stop - start), info


def _seg_key(seg: Segment, proj: Project):
    src = None
    if seg.clip.source and seg.clip.source.exists():
        st = seg.clip.source.stat()
        src = [str(seg.clip.source), st.st_mtime, st.st_size]
    data = [src, seg.clip.kind, round(seg.src_start, 3), seg.frames, seg.src_frames, seg.speed, seg.fit,
            round(seg.focus_x, 3), round(seg.focus_y, 3), seg.look, seg.card_bg, seg.clip.motion,
            seg.clip.clip_audio, seg.clip.zoom, proj.W, proj.H, proj.fps, proj.brand["colors"], 5]
    return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:16]


def make_plan(proj: Project, log=None, allow_missing=False) -> Plan:
    fps, W, H = proj.fps, proj.W, proj.H
    brand = proj.brand
    plan = Plan(project=proj, fps=fps, W=W, H=H, scenes=[], total_frames=0)
    tr_cfg = brand["transitions"]
    vcfg = brand["voice"]
    default_trans = tr_cfg.get("default", "fade")
    default_td = float(tr_cfg.get("duration", 0.5))
    if proj.fmt == "short":
        default_td = float(brand["shorts"].get("transition_duration", 0.3))

    # ---- transitions (in frames) for each scene
    trans, trans_f = [], []
    for i, sc in enumerate(proj.scenes):
        t = "cut" if i == 0 else (sc.transition or default_trans)
        td = sc.transition_duration if sc.transition_duration is not None else default_td
        f = 0 if t == "cut" else max(1, round(td * fps))
        trans.append(t)
        trans_f.append(f)

    pos_f = 0
    for i, sc in enumerate(proj.scenes):
        d_in = trans_f[i]
        d_out = trans_f[i + 1] if i + 1 < len(proj.scenes) else 0

        # ---- natural length of each clip
        nat = []  # (clip, frames, available_src_frames)
        for c in sc.clips:
            try:
                if c.kind == "video":
                    avail, info = _media_len(c.source, c.start, c.end)
                    if not info["has_video"]:
                        raise SFLError(f"{rel(c.source)} has no video picture")
                    if c.start >= (info["duration"] or 0):
                        raise SFLError(f"{rel(c.source)}: start {c.start}s is after the end of the clip "
                                       f"({info['duration']:.1f}s)")
                    avail_f = int(avail / c.speed * fps)
                    want_f = round(c.duration * fps) if c.duration else avail_f
                    nat.append((c, max(1, want_f), max(1, avail_f)))
                elif c.kind == "image":
                    probe(c.source)
                    d = c.duration or float(brand["images"]["default_duration"])
                    nat.append((c, round(d * fps), 10**9))
                else:
                    d = c.duration or sc.duration or 3.0
                    nat.append((c, round(d * fps), 10**9))
            except SFLError as e:
                if not allow_missing:
                    raise
                plan.errors.append(str(e))
                nat.append((c, round((c.duration or 3.0) * fps), 10**9))

        # ---- voice for this scene
        vlen = None
        if sc.voice:
            try:
                vlen, _ = _media_len(sc.voice, sc.voice_start, sc.voice_end, want_audio=True)
            except SFLError as e:
                if not allow_missing:
                    raise
                plan.errors.append(str(e))
        delay = sc.voice_delay if sc.voice_delay is not None else float(vcfg["delay"])

        # ---- scene length
        if sc.duration:
            T_f = round(sc.duration * fps)
        elif vlen is not None:
            T_f = d_in + round((delay + vlen + max(float(vcfg["tail"]), d_out / fps)) * fps)
        else:
            T_f = sum(n for _, n, _ in nat)
        min_f = d_in + d_out + round(0.3 * fps)
        if T_f < min_f:
            plan.warnings.append(f"scene '{sc.id}' is too short for its transitions - lengthened to {min_f / fps:.2f}s")
            T_f = min_f
        if vlen is not None and sc.duration and (d_in / fps + delay + vlen) > sc.duration + 0.05:
            plan.warnings.append(
                f"scene '{sc.id}': voice ({vlen:.1f}s) is longer than the scene duration ({sc.duration}s) - "
                "the end of the voice will overlap the next scene. Remove 'duration' to auto-fit.")

        # ---- fill the scene with clips
        segs = _fill(sc, nat, T_f, fps, plan)
        for s in segs:
            s.look = {**brand["look"], **(sc.look or {})}
            if s.clip.kind == "card":
                s.card_bg = str(s.clip.background or "gradient")
            s.key = _seg_key(s, proj)

        start_f = pos_f - d_in if i > 0 else 0
        plan.scenes.append(PlannedScene(sc, i, T_f, start_f, trans[i], d_in, segs))
        pos_f = start_f + T_f

        t0 = start_f / fps
        t_end = (start_f + T_f) / fps
        # ---- voice placement
        if sc.voice and vlen is not None:
            at = t0 + d_in / fps + delay
            plan.voices.append({"file": sc.voice, "src_start": sc.voice_start, "length": vlen, "at": at,
                                "volume_db": sc.voice_volume_db, "scene": sc.id})
        # ---- overlays
        if sc.card is not None or sc.auto:
            # text appears once the incoming transition is half done and clears before the next one
            plan.overlays.append({"type": f"card_{sc.auto or 'plain'}", "t0": t0 + 0.5 * d_in / fps,
                                  "t1": t_end - 0.6 * d_out / fps,
                                  "data": sc.card or {}, "scene": sc.id})
        # graphic cards: text drawn over each card segment (a card can repeat when clips cycle)
        seg_f = start_f
        for s in segs:
            if s.clip.kind == "card" and s.clip.graphic:
                a = (seg_f + (d_in if seg_f == start_f else 0) * 0.5) / fps
                b = (seg_f + s.frames) / fps - (0.6 * d_out / fps if seg_f + s.frames >= start_f + T_f else 0.05)
                if b - a >= 0.4:
                    plan.overlays.append({"type": "card_graphic", "t0": a, "t1": b, "scene": sc.id,
                                          "data": {"graphic": s.clip.graphic, "text": s.clip.text}})
            seg_f += s.frames
        for o in sc.overlays:
            st = float(o.get("start", 0.35 + d_in / fps))
            dur = o.get("duration")
            if dur in ("scene", "all", None) and o["type"] in ("badge",):
                end = t_end - d_out / fps
            elif dur in ("scene", "all"):
                end = t_end - d_out / fps
            else:
                end = t0 + st + float(dur or OVERLAY_DEFAULT_DUR.get(o["type"], 3.0))
            a, b = t0 + st, min(end, t_end - d_out / fps)
            if b - a < 0.3:
                plan.warnings.append(f"scene '{sc.id}': overlay '{o.get('text', o['type'])}' starts too late "
                                     "for the scene length - skipped")
                continue
            plan.overlays.append({"type": o["type"], "t0": a, "t1": b, "data": o, "scene": sc.id})
            want_sfx = o.get("sfx", o["type"] in ("badge", "title"))
            if want_sfx:
                f = brand["audio"].get("overlay_sfx") if want_sfx is True else want_sfx
                plan.sfx.append({"file": f, "at": a, "volume_db": 0, "auto": True})
        # ---- scene sound effects
        for s in sc.sfx:
            plan.sfx.append({"file": s["file"], "at": t0 + s["at"], "volume_db": s["volume_db"]})
        if trans[i] != "cut" and brand["audio"].get("transition_sfx") and not sc.auto:
            plan.sfx.append({"file": brand["audio"]["transition_sfx"], "at": max(0, t0 - 0.05),
                             "volume_db": -3, "auto": True})
        if sc.auto == "intro" and proj.intro.get("sfx"):
            plan.sfx.append({"file": proj.intro["sfx"], "at": t0, "volume_db": -2, "auto": True})

    plan.total_frames = pos_f

    # ---- master voice-over (one file for the whole video)
    vo = proj.audio.get("voiceover")
    if vo:
        try:
            vo_len, _ = _media_len(vo, want_audio=True)
            at = float(proj.audio.get("voiceover_start", 0))
            plan.voices.append({"file": vo, "src_start": 0.0, "length": vo_len, "at": at,
                                "volume_db": float(proj.audio.get("voiceover_volume_db", 0)), "scene": None})
            if at + vo_len > plan.total + 0.05:
                plan.warnings.append(
                    f"master voice-over ends at {at + vo_len:.1f}s but the video is only {plan.total:.1f}s long - "
                    "add scenes or lengthen scene durations, otherwise the voice is cut off")
        except SFLError as e:
            if not allow_missing:
                raise
            plan.errors.append(str(e))

    _plan_cues(plan, log)
    plan.overlays.sort(key=lambda o: o["t0"])
    return plan


def _fill(sc: Scene, nat, T_f, fps, plan):
    """Choose which clip plays when, so the scene lasts exactly T_f frames.

    fill: cycle  -> repeat the scene's clips in order until the voice ends (default)
          freeze -> play clips once, then hold the last frame
          slow   -> slow all clips down evenly (max 1.6x), else falls back to cycle
    """
    items = [{"clip": c, "n": n, "avail": a, "speed": c.speed} for c, n, a in nat]
    if len(items) == 1 and items[0]["clip"].kind in ("image", "card") and not items[0]["clip"].duration:
        items[0]["n"] = T_f  # a single photo simply stays (and slowly moves) for the whole scene
    total = sum(it["n"] for it in items)
    mode = sc.fill
    if total < T_f and mode == "slow" and total > 0:
        factor = T_f / total
        if factor > 1.6:
            plan.warnings.append(f"scene '{sc.id}': clips would need slowing by {factor:.1f}x - using 'cycle' instead")
            mode = "cycle"
        else:
            for it in items:
                it["n"] = round(it["n"] * factor)
                if it["clip"].kind == "video":
                    it["speed"] = it["clip"].speed / factor
                    it["avail"] = int(it["avail"] * factor)
    segs, used, k, cycled = [], 0, 0, False
    while used < T_f and items:
        if k >= len(items):
            if mode != "cycle":
                break
            k, cycled = 0, True
        it = items[k]
        n = min(it["n"], T_f - used)
        segs.append(Segment(it["clip"], it["clip"].start, n, min(n, it["avail"]), it["speed"], sc.id,
                            avail=it["avail"]))
        used += n
        k += 1
    if cycled:
        plan.warnings.append(f"scene '{sc.id}': clips are shorter than the voice, so they repeat. "
                             "Add more footage to this scene for a more professional result.")
    if used < T_f and segs:
        segs[-1].frames += T_f - used
        if segs[-1].clip.kind == "video" and T_f - used > 0.2 * fps:
            plan.warnings.append(f"scene '{sc.id}': last clip is frozen for {(T_f - used) / fps:.1f}s (fill: {mode})")
    # avoid a tiny final flash (< 0.4 s) at the end of a scene
    if len(segs) > 1 and segs[-1].frames < round(0.4 * fps):
        extra = segs.pop().frames
        segs[-1].frames += extra
    for s in segs:
        s.src_frames = min(s.frames, s.avail)
        if s.clip.kind == "video" and s.frames - s.src_frames > 0.2 * fps and mode != "freeze":
            plan.warnings.append(f"scene '{sc.id}': clip {rel(s.clip.source)} is too short; "
                                 f"its last frame is held for {(s.frames - s.src_frames) / fps:.1f}s")
    return segs


def _plan_cues(plan: Plan, log):
    proj = plan.project
    mode = str(proj.subtitles.get("mode", "auto")).lower()
    if mode in ("none", "off", "false"):
        return
    wa = whisper_available()
    cues = []
    maxc = int(proj.brand["subtitles"]["long"]["max_chars_per_line"]) * 2

    def from_voice(v, sc: Scene | None, sub_file, narration):
        shift = v["at"] - v["src_start"]
        if sc is not None and sc.cue_source:
            plan.cue_method[v["scene"]] = "sliced from master subtitles"
            return [(a + v["at"], b + v["at"], t) for a, b, t in sc.cue_source]
        if sub_file and mode in ("auto", "srt"):
            if sub_file.exists():
                plan.cue_method[v["scene"] or "voiceover"] = f"file {rel(sub_file)}"
                out = []
                for a, b, t in parse_subtitle_file(sub_file):
                    a2, b2 = a + shift, b + shift
                    if b2 <= v["at"] or a2 >= v["at"] + v["length"]:
                        continue
                    out.append((max(a2, v["at"]), min(b2, v["at"] + v["length"]), t))
                return out
            plan.errors.append(f"subtitle file not found: {rel(sub_file)}")
        if mode == "whisper" or (mode == "auto" and wa and not narration):
            if wa and v["file"].exists():
                plan.cue_method[v["scene"] or "voiceover"] = "Whisper transcription"
                out = []
                for a, b, t in whisper_cues(v["file"], log):
                    a2, b2 = a + shift, b + shift
                    if b2 > v["at"] and a2 < v["at"] + v["length"]:
                        out.append((max(a2, v["at"]), min(b2, v["at"] + v["length"]), t))
                return out
            if mode == "whisper":
                plan.warnings.append("subtitles.mode is 'whisper' but faster-whisper is not installed - "
                                     "using narration text instead (see docs/INSTALL.md)")
        if narration and mode in ("auto", "script", "whisper"):
            plan.cue_method[v["scene"] or "voiceover"] = "script text (estimated timing)"
            return script_to_cues(narration, v["at"], v["at"] + v["length"], maxc)
        return []

    by_scene = {ps.scene.id: ps for ps in plan.scenes}
    for v in plan.voices:
        if v["scene"] is None:
            cues += from_voice(v, None, proj.subtitles.get("file"), proj.narration)
        else:
            sc = by_scene[v["scene"]].scene
            cues += from_voice(v, sc, sc.subtitle_file, sc.narration)
    # scenes with narration but no voice: show text over the scene (silent explainer)
    voiced = {v["scene"] for v in plan.voices}
    if not any(v["scene"] is None for v in plan.voices):
        for ps in plan.scenes:
            sc = ps.scene
            if sc.id not in voiced and sc.narration and mode in ("auto", "script"):
                a = (ps.start_f + ps.trans_f) / plan.fps + 0.2
                b = (ps.start_f + ps.frames) / plan.fps - 0.3
                plan.cue_method[sc.id] = "script text over silent scene"
                cues += script_to_cues(sc.narration, a, b, maxc)
    plan.cues = sorted((max(0.0, a), min(plan.total, b), t) for a, b, t in cues if b > a and a < plan.total)
