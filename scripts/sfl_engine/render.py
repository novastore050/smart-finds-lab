"""Render one timeline segment (a trimmed clip / image / title card) into a standard file.

Every segment comes out identical in format (size, fps, pixel format, 48 kHz stereo PCM)
so they can be joined with transitions. Segments are cached in temp/<project>/segments/
by a fingerprint, so re-running after changing only titles or music is much faster.
"""
from __future__ import annotations

from pathlib import Path

from . import reframe
from .plan import Plan, Segment
from .util import ffmpeg_color, probe, rel, resolve, run_ffmpeg


def _even(x):
    return max(2, int(round(x / 2)) * 2)


def _ease(expr):
    """Smooth ease-in-out of a 0..1 progress expression."""
    return f"(0.5-0.5*cos(PI*{expr}))"


def look_filters(look: dict):
    f = []
    b, c, s, g = (float(look.get(k, d)) for k, d in
                  (("brightness", 0), ("contrast", 1), ("saturation", 1), ("gamma", 1)))
    if (b, c, s, g) != (0, 1, 1, 1):
        f.append(f"eq=brightness={b}:contrast={c}:saturation={s}:gamma={g}")
    sharpen = float(look.get("sharpen", 0) or 0)
    if sharpen > 0:
        f.append(f"unsharp=5:5:{sharpen:.2f}:5:5:0")
    if look.get("vignette"):
        f.append("vignette=PI/5")
    return f


def fit_graph(inp: str, out: str, W: int, H: int, fit: str, fx: float, fy: float, bg_hex=None):
    """Filter-graph text that makes [inp] exactly WxH. fit: cover (crop) or blur/contain."""
    if fit in ("blur", "contain"):
        bw, bh = _even(W / 8), _even(H / 8)
        if fit == "contain" and bg_hex:
            bg = f"color=c={ffmpeg_color(bg_hex)}:s={W}x{H}[bgc];"
            return (f"{bg}[{inp}]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos[fg_{out}];"
                    f"[bgc][fg_{out}]overlay=(W-w)/2:(H-h)/2:shortest=1[{out}]")
        return (f"[{inp}]split=2[bg0_{out}][fg0_{out}];"
                f"[bg0_{out}]scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh},"
                f"gblur=sigma=5,scale={W}:{H},eq=brightness=-0.10:saturation=0.85[bg_{out}];"
                f"[fg0_{out}]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos[fg_{out}];"
                f"[bg_{out}][fg_{out}]overlay=(W-w)/2:(H-h)/2[{out}]")
    return (f"[{inp}]scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={W}:{H}:(iw-{W})*{fx:.4f}:(ih-{H})*{fy:.4f}[{out}]")


def resolve_fit(seg: Segment, plan: Plan, log=None):
    """Decide fit mode + focus for a segment (handles 'auto' reframing)."""
    proj, c = plan.project, seg.clip
    scene = next(ps.scene for ps in plan.scenes if ps.scene.id == seg.scene_id)
    fit = c.fit
    if proj.fmt == "short":
        fit = scene.short_fit or fit or proj.brand["shorts"].get("fit", "auto")
    if c.kind == "image":
        fit = fit or proj.brand["images"].get("fit", "cover")
        if fit == "auto":
            fit = "cover"
    fit = fit or "auto"
    fx = c.focus_x if c.focus_x is not None else (scene.short_focus_x if proj.fmt == "short" else None)
    fy = c.focus_y if c.focus_y is not None else 0.5
    if fit in ("center", "focus"):
        fit = "cover"
    info = probe(c.source) if c.source else {}
    ratio = (info["width"] / info["height"]) / (plan.W / plan.H) if info.get("width") else 1.0
    if fit == "auto" and (proj.fmt == "long" or c.kind == "image" or 0.8 <= ratio <= 1.25):
        # long-form: never crop away most of a vertical clip - show it whole on a blurred background
        fit = "cover" if 0.8 <= ratio <= 1.25 else "blur"
    if fit == "auto" and c.kind == "video":
        if fx is not None:  # user gave a focus point - just use it
            fit = "cover"
        else:
            mode, ax, ay, cov = reframe.analyze(c.source, seg.src_start, seg.src_frames / plan.fps * seg.speed,
                                                plan.W, plan.H)
            fit, fx, fy = mode, ax, ay
            if log:
                log.debug(f"auto-reframe {rel(c.source)}: {mode} focus=({ax:.2f},{ay:.2f}) coverage={cov:.2f}")
            seg.auto_info = f"{mode} (focus {ax:.2f}, detail kept {cov:.0%})"
    return fit, (0.5 if fx is None else fx), fy


def render_segment(seg: Segment, plan: Plan, cache: Path, log) -> Path:
    out = cache / f"{seg.key}.mkv"
    if out.exists() and out.stat().st_size > 0:
        return out
    W, H, fps = plan.W, plan.H, plan.fps
    N = seg.frames
    dur = N / fps
    c = seg.clip
    brand = plan.project.brand
    look = look_filters(seg.look)
    args, fc = [], []
    audio_from_clip = False

    if c.kind == "video":
        fit, fx, fy = resolve_fit(seg, plan, log)
        info = probe(c.source)
        src_len = seg.src_frames / fps * seg.speed
        args += ["-ss", f"{seg.src_start:.3f}", "-t", f"{src_len + 0.25:.3f}", "-i", str(c.source)]
        pre = ["setpts=(PTS-STARTPTS)/%s" % f"{seg.speed:.5f}" if seg.speed != 1 else "setpts=PTS-STARTPTS",
               f"fps={fps}", "format=yuv420p"]
        fc.append(f"[0:v]{','.join(pre)}[pre]")
        fc.append(fit_graph("pre", "fit", W, H, fit, fx, fy))
        hold = max(0.5, (N - seg.src_frames) / fps + 0.5)
        post = look + [f"tpad=stop_mode=clone:stop_duration={hold:.3f}", "setsar=1", "format=yuv420p"]
        fc.append(f"[fit]{','.join(post)}[v]")
        audio_from_clip = c.clip_audio > 0 and info["has_audio"]
    elif c.kind == "image":
        fit, fx, fy = resolve_fit(seg, plan, log)
        info = probe(c.source)
        has_alpha = bool(info.get("pix_fmt") and ("a" in info["pix_fmt"].replace("gray", "") or "pal" in info["pix_fmt"]))
        motion = c.motion or brand["images"].get("motion", "zoom_in")
        bg_hex = c.background if (c.background and str(c.background).startswith("#")) else "#F2F4F7"
        args += ["-i", str(c.source)]
        # flatten transparent PNGs (product cut-outs) on a clean light background
        if has_alpha:
            iw, ih = info["width"], info["height"]
            fc.append(f"color=c={ffmpeg_color(bg_hex)}:s={iw}x{ih}:d=1[flat];"
                      f"[flat][0:v]overlay=0:0:format=auto,format=yuv420p[img]")
            fc.append(fit_graph("img", "fit", W, H, "contain" if fit != "cover" else "cover", fx, fy, bg_hex))
        else:
            fc.append("[0:v]format=yuv420p[img]")
            fc.append(fit_graph("img", "fit", W, H, fit, fx, fy))
        if motion == "none":
            post = [f"loop=loop={N}:size=1:start=0", f"fps={fps}"]
        else:
            amt = 0.10
            p = _ease(f"on/{max(1, N - 1)}")
            z, x, y = "1", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
            if motion == "zoom_in":
                z = f"1+{amt}*{p}"
            elif motion == "zoom_out":
                z = f"{1 + amt}-{amt}*{p}"
            else:
                z = f"{1 + amt}"
                span_x, span_y = "(iw-iw/zoom)", "(ih-ih/zoom)"
                x = {"pan_right": f"{span_x}*{p}", "pan_left": f"{span_x}*(1-{p})"}.get(motion, x)
                y = {"pan_down": f"{span_y}*{p}", "pan_up": f"{span_y}*(1-{p})"}.get(motion, y)
            post = [f"scale={W * 2}:{H * 2}:flags=lanczos",
                    f"zoompan=z='{z}':x='{x}':y='{y}':d={N}:s={W}x{H}:fps={fps}"]
        post += look + ["tpad=stop_mode=clone:stop_duration=0.5", "setsar=1", "format=yuv420p"]
        fc.append(f"[fit]{','.join(post)}[v]")
    else:  # card
        bg = seg.card_bg or "gradient"
        col = brand["colors"]
        if bg == "gradient":
            src = (f"gradients=s={W}x{H}:c0={ffmpeg_color(col['dark'])}:c1={ffmpeg_color(col['dark2'])}:"
                   f"x0=0:y0=0:x1={W}:y1={H}:speed=0.008:r={fps}:d={dur + 0.5:.3f}")
            args += ["-f", "lavfi", "-i", src]
            fc.append("[0:v]format=yuv420p,setsar=1[v]")
        elif bg.startswith("#"):
            args += ["-f", "lavfi", "-i", f"color=c={ffmpeg_color(bg)}:s={W}x{H}:r={fps}:d={dur + 0.5:.3f}"]
            fc.append("[0:v]format=yuv420p,setsar=1[v]")
        else:
            img = resolve(bg)
            args += ["-loop", "1", "-framerate", str(fps), "-t", f"{dur + 0.5:.3f}", "-i", str(img)]
            fc.append(f"[0:v]format=yuv420p[img];" + fit_graph("img", "fit", W, H, "cover", 0.5, 0.5))
            fc.append("[fit]gblur=sigma=12,eq=brightness=-0.25:saturation=0.8,setsar=1,format=yuv420p[v]")

    # ---- audio
    if audio_from_clip:
        af = []
        if seg.speed != 1:
            sp = seg.speed
            while sp > 2:
                af.append("atempo=2.0")
                sp /= 2
            while sp < 0.5:
                af.append("atempo=0.5")
                sp /= 0.5
            af.append(f"atempo={sp:.5f}")
        af += [f"volume={c.clip_audio:.3f}", "aresample=48000", "aformat=sample_fmts=s16:channel_layouts=stereo",
               "apad", f"atrim=end={dur:.4f}", "afade=t=in:d=0.04", f"afade=t=out:st={max(0, dur - 0.06):.4f}:d=0.06"]
        fc.append(f"[0:a]{','.join(af)}[a]")
    else:
        args += ["-f", "lavfi", "-t", f"{dur:.4f}", "-i", "anullsrc=r=48000:cl=stereo"]
        fc.append(f"[1:a]aformat=sample_fmts=s16:channel_layouts=stereo,apad,atrim=end={dur:.4f}[a]")

    args += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-frames:v", str(N),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(fps),
             "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-t", f"{dur:.4f}", str(out.with_suffix('.part.mkv'))]
    what = rel(c.source) if c.source else f"title card ({seg.scene_id})"
    run_ffmpeg(args, log, desc=f"segment {seg.scene_id}: {what}")
    out.with_suffix(".part.mkv").replace(out)
    return out
