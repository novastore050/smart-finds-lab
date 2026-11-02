"""Build long-form videos and Shorts from timeline files."""
from __future__ import annotations

import copy
import os
import shutil
import time
from pathlib import Path

from . import qc
from .audio import FMT, mix_audio
from .config import Clip, Project, Scene, deep_merge, load_brand, load_file, load_timeline, parse_scene, slugify
from .graphics import Graphics
from .plan import Plan, make_plan
from .render import render_segment
from .subtitles import write_srt
from .util import ROOT, SFLError, Log, ffpath, rel, resolve, run_ffmpeg, unique_output

CACHE = ROOT / "temp" / "segment-cache"


def add_bookends(proj: Project):
    """Insert the branded intro and outro cards (long-form only)."""
    if proj.fmt != "long":
        return
    if any(s.auto for s in proj.scenes):
        return
    it, ot = proj.intro, proj.outro
    if it.get("enabled"):
        d = float(it.get("duration", 2.6))
        sc = Scene(id="intro", clips=[Clip(kind="card", background=it.get("background"), duration=d)],
                   duration=d, card={}, auto="intro", transition=it.get("transition"))
        idx = 1 if it.get("position") == "after_first_scene" and len(proj.scenes) > 1 else 0
        proj.scenes.insert(idx, sc)
    if ot.get("enabled"):
        d = float(ot.get("duration", 10))
        proj.scenes.append(Scene(id="outro", clips=[Clip(kind="card", background=ot.get("background"), duration=d)],
                                 duration=d, card={}, auto="outro", transition=ot.get("transition", "fade")))


def add_short_extras(proj: Project, plan: Plan):
    """Opening hook text and closing call-to-action for Shorts."""
    if proj.fmt != "short":
        return
    s = proj.brand["shorts"]
    if proj.hook:
        hook = proj.hook if isinstance(proj.hook, dict) else {"text": str(proj.hook)}
        dur = float(hook.get("duration", s["hook_duration"]))
        plan.overlays.insert(0, {"type": "hook", "t0": 0.05, "t1": min(dur, plan.total), "data": hook, "scene": None})
        plan.sfx.append({"file": proj.brand["audio"].get("overlay_sfx"), "at": 0.05, "volume_db": 0, "auto": True})
    # keep the hook clear: scene graphics that would appear under it wait until it is gone
    hook_end = plan.overlays[0]["t1"] if proj.hook else 0
    for o in plan.overlays:
        if o["type"] != "hook" and o["t0"] < hook_end and o["t1"] > hook_end + 0.6:
            o["t0"] = hook_end + 0.1
    plan.overlays = [o for o in plan.overlays if o["type"] == "hook" or o["t1"] - o["t0"] >= 0.5]
    cta = proj.cta if proj.cta is not None else {"text": s.get("cta_text")}
    if cta and (cta.get("text") if isinstance(cta, dict) else cta):
        cta = cta if isinstance(cta, dict) else {"text": str(cta)}
        dur = float(cta.get("duration", s["cta_duration"]))
        cta.setdefault("position", "top")
        t0 = max(0.0, plan.total - dur)
        for o in plan.overlays:  # other graphics leave the screen when the CTA arrives
            if o["type"] != "hook":
                o["t1"] = min(o["t1"], t0)
        plan.overlays = [o for o in plan.overlays if o["t1"] - o["t0"] >= 0.4]
        plan.overlays.append({"type": "cta", "t0": t0, "t1": plan.total - 0.05, "data": cta, "scene": None})


def _scene_graph(plan: Plan, seg_inputs):
    """Filter-graph text joining segments into scenes and scenes with transitions."""
    fps, fc = plan.fps, []
    k = 0
    acc, acc_f = None, 0
    for si, ps in enumerate(plan.scenes):
        labels = []
        for _ in ps.segments:
            fc.append(f"[{seg_inputs[k]}:v]setpts=PTS-STARTPTS[g{k}]")
            labels.append(f"[g{k}]")
            k += 1
        if len(labels) == 1:
            fc.append(f"{labels[0]}fps={fps},settb=1/{fps}[sc{si}]")
        else:
            fc.append(f"{''.join(labels)}concat=n={len(labels)}:v=1:a=0,fps={fps},settb=1/{fps}[sc{si}]")
        if acc is None:
            acc, acc_f = f"sc{si}", ps.frames
            continue
        if ps.trans == "cut":
            fc.append(f"[{acc}][sc{si}]concat=n=2:v=1:a=0,fps={fps},settb=1/{fps}[j{si}]")
        else:
            off = (acc_f - ps.trans_f) / fps
            fc.append(f"[{acc}][sc{si}]xfade=transition={ps.trans}:duration={ps.trans_f / fps:.4f}:"
                      f"offset={off:.4f}[j{si}]")
        acc, acc_f = f"j{si}", acc_f - ps.trans_f + ps.frames
    return fc, acc


def _join_clip_audio(plan: Plan, seg_paths, tmp: Path, log):
    """Join the original clip sound (only when a clip has clip_audio > 0)."""
    if not any(s.clip.clip_audio > 0 for ps in plan.scenes for s in ps.segments):
        return None
    args, fc, k = [], [], 0
    acc, acc_f = None, 0
    for si, ps in enumerate(plan.scenes):
        labels = []
        for _ in ps.segments:
            args += ["-i", str(seg_paths[k])]
            fc.append(f"[{k}:a]{FMT}[a{k}]")
            labels.append(f"[a{k}]")
            k += 1
        fc.append(f"{''.join(labels)}concat=n={len(labels)}:v=0:a=1[s{si}]")
        if acc is None:
            acc, acc_f = f"s{si}", ps.frames
            continue
        if ps.trans == "cut":
            fc.append(f"[{acc}][s{si}]concat=n=2:v=0:a=1[j{si}]")
        else:
            fc.append(f"[{acc}][s{si}]acrossfade=d={ps.trans_f / plan.fps:.4f}[j{si}]")
        acc, acc_f = f"j{si}", acc_f - ps.trans_f + ps.frames
    out = tmp / "clip_audio.wav"
    run_ffmpeg(args + ["-filter_complex", ";".join(fc), "-map", f"[{acc}]", "-c:a", "pcm_f32le", str(out)],
               log, desc="joining clip sound")
    return out


def render_project(proj: Project, log: Log, overwrite=False, draft=False, keep_temp=True) -> Path | None:
    t_start = time.time()
    add_bookends(proj)
    log.info(f"\n=== {proj.title}  ({'Long-form 16:9' if proj.fmt == 'long' else 'Short 9:16'}) ===")
    log.info("1) Planning timeline and checking files ...")
    plan = make_plan(proj, log, allow_missing=True)
    add_short_extras(proj, plan)
    checks = qc.preflight(plan)
    out_dir = proj.output.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{proj.name}{'_draft' if draft else ''}.qc.md"
    for it in checks.items:
        if it["level"] in (qc.ERR, qc.WARN):
            log.info(f"   {qc.ICON[it['level']]} {it['area']}: {it['message']}")
    if checks.count(qc.ERR):
        qc.write_report(report_path, plan, checks, None, {}, 0)
        log.info(f"\nSTOPPED: {checks.count(qc.ERR)} problem(s) must be fixed first. Report: {rel(report_path)}")
        return None
    log.info(f"   planned length {qc.fmt_time(plan.total)}, {len(plan.scenes)} scenes, "
             f"{sum(len(ps.segments) for ps in plan.scenes)} segments")

    tmp = ROOT / "temp" / proj.name
    tmp.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    # ---- 2) segments
    log.info("2) Preparing clips (trim, reframe, colour, motion) ...")
    seg_paths = []
    all_segs = [s for ps in plan.scenes for s in ps.segments]
    done = {}
    for i, s in enumerate(all_segs, 1):
        if s.key not in done:
            what = rel(s.clip.source) if s.clip.source else f"title card '{s.scene_id}'"
            cached = (CACHE / f"{s.key}.mkv").exists()
            log.info(f"   [{i}/{len(all_segs)}] {what}{' (cached)' if cached else ''}")
            done[s.key] = render_segment(s, plan, CACHE, log)
        seg_paths.append(done[s.key])

    # ---- 3) audio
    log.info("3) Mixing voice, music and sound effects ...")
    clip_audio = _join_clip_audio(plan, seg_paths, tmp, log)
    audio = mix_audio(plan, tmp, log, clip_audio)

    # ---- 4) graphics + subtitles
    log.info("4) Creating titles, captions and subtitles ...")
    g = Graphics(plan)
    if not proj.subtitles.get("burn_in", True):
        cues, plan.cues = plan.cues, []
        g.build()
        plan.cues = cues
    else:
        g.build()
    ass = g.write(tmp / "graphics.ass")
    srt = None
    if plan.cues and proj.subtitles.get("export_srt", True):
        srt = unique_output(out_dir / f"{proj.name}{'_draft' if draft else ''}.srt", overwrite)

    # ---- 5) final export
    log.info("5) Exporting final MP4 ...")
    fmt = proj.brand["formats"][proj.fmt]
    args, inputs = [], []
    for p in seg_paths:
        inputs.append(len(inputs))
        args += ["-i", str(p)]
    fc, last = _scene_graph(plan, inputs)
    tr = proj.brand["transitions"]
    fi = float(tr.get("video_fade_in", 0)) if proj.fmt == "long" else 0
    fo = float(tr.get("video_fade_out", 0)) if proj.fmt == "long" else 0
    post = []
    if fi > 0:
        post.append(f"fade=t=in:st=0:d={fi}")
    if fo > 0:
        post.append(f"fade=t=out:st={plan.total - fo:.3f}:d={fo}")
    fonts_rel = os.path.relpath(resolve(proj.brand["fonts"]["folder"]), tmp)
    post.append(f"ass=filename=graphics.ass:fontsdir={ffpath(fonts_rel)}")
    logo = proj.brand["channel"].get("logo") or {}
    idx_audio = len(inputs)
    if logo.get("file") and resolve(logo["file"]).exists():
        args += ["-loop", "1", "-i", str(resolve(logo["file"]))]
        lw = int(logo.get("width", 150))
        m = 40
        pos = logo.get("position", "top-right")
        x = f"W-w-{m}" if "right" in pos else str(m)
        y = f"H-h-{m}" if "bottom" in pos else str(m)
        fc.append(f"[{idx_audio}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa={float(logo.get('opacity', 0.9))}[logo]")
        fc.append(f"[{last}][logo]overlay={x}:{y}:shortest=1[lg]")
        last = "lg"
        idx_audio += 1
    fc.append(f"[{last}]{','.join(post)},format=yuv420p[vout]")
    args += ["-i", str(audio)]
    final = unique_output(proj.output.with_name(proj.output.stem + ("_draft" if draft else "") + ".mp4"), overwrite)
    part = final.with_name(final.stem + ".part.mp4")
    args += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", f"{idx_audio}:a",
             "-c:v", "libx264", "-preset", "ultrafast" if draft else fmt.get("preset", "medium"),
             "-crf", "26" if draft else str(fmt.get("crf", 18)), "-profile:v", "high", "-pix_fmt", "yuv420p",
             "-r", str(plan.fps), "-g", str(plan.fps * 2), "-frames:v", str(plan.total_frames),
             "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-c:a", "aac", "-b:a", fmt.get("audio_bitrate", "192k"), "-ar", "48000", "-ac", "2",
             "-movflags", "+faststart", "-metadata", f"title={proj.title}", str(part)]
    run_ffmpeg(args, log, desc="exporting", cwd=tmp, total=plan.total)
    part.replace(final)
    if srt:
        write_srt(plan.cues, srt)

    # ---- 6) QC
    log.info("6) Quality control ...")
    stats = qc.postcheck(final, plan, log, checks, srt)
    elapsed = time.time() - t_start
    report = qc.write_report(report_path, plan, checks, final, stats, elapsed)
    shutil.copy(report, ROOT / "logs" / f"{report.stem}_{time.strftime('%Y%m%d-%H%M%S')}.md")
    for it in checks.items:
        if it["level"] in (qc.ERR, qc.WARN) and it["area"] not in ("Timeline", "Placeholder text", "Copyright",
                                                                   "Honesty", "Quality", "Subtitles", "Audio",
                                                                   "Trimming", "Sound effects"):
            log.info(f"   {qc.ICON[it['level']]} {it['area']}: {it['message']}")
    log.info(f"\nDONE ({checks.status}) in {elapsed:.0f}s")
    log.info(f"   Video:     {rel(final)}")
    if srt:
        log.info(f"   Subtitles: {rel(srt)}")
    log.info(f"   QC report: {rel(report)}")
    if not keep_temp:
        shutil.rmtree(tmp, ignore_errors=True)
    return final


def check_project(proj: Project, log: Log):
    add_bookends(proj)
    plan = make_plan(proj, log, allow_missing=True)
    add_short_extras(proj, plan)
    checks = qc.preflight(plan)
    return plan, checks


# --------------------------------------------------------------------------- shorts
def load_shorts(path, only=None) -> list:
    """Read a shorts file and return a list of Project objects (one per Short)."""
    path = resolve(path)
    cfg = load_file(path)
    defaults = cfg.get("defaults") or {}
    items = cfg.get("shorts") or []
    if not items:
        raise SFLError(f"{rel(path)} has no 'shorts:' list")
    long_cache = {}
    projects = []
    for n, item in enumerate(items, 1):
        s = deep_merge(defaults, item)
        name = slugify(s.get("output") or f"{path.stem}-{n:02d}")
        if only and only not in (name, str(n)):
            continue
        brand = load_brand(s.get("brand"), s.get("style"))
        issues = []
        scenes = []
        if s.get("use_scenes"):
            src = s.get("from_timeline")
            if not src:
                raise SFLError(f"short '{name}': 'use_scenes' needs 'from_timeline'")
            if src not in long_cache:
                lp = load_timeline(src)
                add_bookends(lp)
                long_cache[src] = (lp, make_plan(lp, None, allow_missing=True))
            lp, lplan = long_cache[src]
            by_id = {sc.id: sc for sc in lp.scenes}
            vo = lp.audio.get("voiceover")
            vo_at = float(lp.audio.get("voiceover_start", 0))
            for sid in s["use_scenes"]:
                if str(sid) not in by_id:
                    issues.append(("error", f"short '{name}': scene '{sid}' not found in {src} "
                                            f"(available: {', '.join(by_id)})"))
                    continue
                sc = copy.deepcopy(by_id[str(sid)])
                sc.transition, sc.transition_duration = None, None
                keep = s.get("keep_overlays", True)
                sc.overlays = [o for o in sc.overlays if keep and o["type"] in ("badge", "callout", "lower_third", "text")
                               and not isinstance(o.get("position"), (dict, list))]
                for o in sc.overlays:  # long-form positions don't suit 9:16 - use Shorts defaults
                    if o["type"] != "badge":
                        o.pop("position", None)
                if not sc.voice and vo:
                    a, b = lplan.scene_window(sc.id, own=True)
                    sc.voice, sc.voice_start, sc.voice_end = vo, max(0.0, a - vo_at), max(0.0, b - vo_at)
                    sc.voice_delay, sc.duration = 0.0, None
                    # keep subtitles that are mostly inside this slice (drop tiny cut-off fragments)
                    sc.cue_source = [(max(c0, a) - a, min(c1, b) - a, t) for c0, c1, t in lplan.cues
                                     if min(c1, b) - max(c0, a) >= max(0.8, 0.5 * (c1 - c0))]
                scenes.append(sc)
        for i, d in enumerate(s.get("scenes") or []):
            scenes.append(parse_scene(d, len(scenes) + i, issues, brand))
        if not scenes:
            raise SFLError(f"short '{name}' has no scenes (use 'use_scenes' or 'scenes')")
        audio = dict(s.get("audio") or {})
        for k in ("voiceover", "music"):
            if audio.get(k):
                audio[k] = resolve(audio[k])
        subs = dict(s.get("subtitles") or {})
        subs.setdefault("mode", "auto")
        subs.setdefault("burn_in", True)
        subs.setdefault("export_srt", True)
        if subs.get("file"):
            subs["file"] = resolve(subs["file"])
        projects.append(Project(
            name=name, title=s.get("title") or name, fmt="short", brand=brand, scenes=scenes,
            output=ROOT / "output" / "shorts" / f"{name}.mp4", config_path=path, audio=audio, subtitles=subs,
            intro={"enabled": False}, outro={"enabled": False}, hook=s.get("hook"), cta=s.get("cta"),
            narration=str(s.get("narration") or ""), issues=issues))
    if only and not projects:
        raise SFLError(f"No short called '{only}' in {rel(path)}")
    return projects
