"""Audio mixing: voice-over + background music (auto-ducked) + sound effects + clip sound,
then two-pass loudness normalisation to YouTube's -14 LUFS."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .plan import Plan
from .util import probe, rel, resolve, run_ffmpeg, run_ffmpeg_analysis

FMT = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"


def mix_audio(plan: Plan, tmp: Path, log, clip_audio: Path | None = None) -> Path:
    proj, b = plan.project, plan.project.brand["audio"]
    total = plan.total
    args = ["-f", "lavfi", "-t", f"{total:.4f}", "-i", "anullsrc=r=48000:cl=stereo"]
    fc, mix = [], ["[0:a]"]
    n = 1

    if clip_audio:
        args += ["-i", str(clip_audio)]
        fc.append(f"[{n}:a]{FMT}[clip]")
        mix.append("[clip]")
        n += 1

    # ---- voice
    vlabels = []
    for i, v in enumerate(plan.voices):
        args += ["-ss", f"{v['src_start']:.3f}", "-t", f"{v['length']:.3f}", "-i", str(v["file"])]
        ms = int(round(v["at"] * 1000))
        vol = float(b.get("voice_volume_db", 0)) + float(v.get("volume_db", 0))
        fc.append(f"[{n}:a]{FMT},volume={vol:.2f}dB,adelay={ms}:all=1[v{i}]")
        vlabels.append(f"[v{i}]")
        n += 1
    music = proj.audio.get("music")
    duck = bool(proj.audio.get("duck_music_under_voice", b.get("duck_music_under_voice", True)))
    if vlabels:
        chain = f"{''.join(vlabels)}amix=inputs={len(vlabels)}:normalize=0:dropout_transition=0"
        if b.get("voice_cleanup", True):
            chain += ",highpass=f=80,acompressor=threshold=0.1:ratio=3:attack=10:release=180:makeup=1.6"
        chain += f",apad,atrim=0:{total:.4f}"
        if music and duck:
            fc.append(chain + ",asplit=2[vo][vosc]")
        else:
            fc.append(chain + "[vo]")
        mix.append("[vo]")

    # ---- music
    if music:
        mdb = float(proj.audio.get("music_volume_db", b.get("music_volume_db", -19)))
        fi = float(b.get("music_fade_in", 1.5))
        fo = min(float(b.get("music_fade_out", 3.0)), total / 3)
        start = float(proj.audio.get("music_start", 0))
        args += ["-stream_loop", "-1", "-ss", f"{start:.3f}", "-i", str(music)]
        fc.append(f"[{n}:a]{FMT},atrim=0:{total:.4f},asetpts=PTS-STARTPTS,volume={mdb:.2f}dB,"
                  f"afade=t=in:d={fi:.2f},afade=t=out:st={max(0, total - fo):.3f}:d={fo:.2f}[mus0]")
        if vlabels and duck:
            fc.append(f"[mus0][vosc]sidechaincompress=threshold={float(b.get('duck_threshold', 0.03))}:"
                      f"ratio={float(b.get('duck_ratio', 6))}:attack=25:release=450[mus]")
        else:
            fc.append("[mus0]anull[mus]")
        mix.append("[mus]")
        n += 1

    # ---- sound effects
    slabels = []
    for i, s in enumerate(plan.sfx):
        f = resolve(s["file"])
        if not f or not f.exists():
            if not s.get("auto"):
                log.warn(f"sound effect not found, skipped: {rel(f) if f else s['file']}")
            continue
        args += ["-i", str(f)]
        vol = float(b.get("sfx_volume_db", -8)) + float(s.get("volume_db", 0))
        fc.append(f"[{n}:a]{FMT},volume={vol:.2f}dB,adelay={int(round(s['at'] * 1000))}:all=1[s{i}]")
        slabels.append(f"[s{i}]")
        n += 1
    if slabels:
        fc.append(f"{''.join(slabels)}amix=inputs={len(slabels)}:normalize=0:dropout_transition=0[sfx]")
        mix.append("[sfx]")

    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0:dropout_transition=0,"
              f"atrim=0:{total:.4f}[out]")
    raw = tmp / "mix_raw.wav"
    run_ffmpeg(args + ["-filter_complex", ";".join(fc), "-map", "[out]", "-c:a", "pcm_f32le", str(raw)],
               log, desc="mixing audio")
    return normalize(raw, tmp / "mix_final.wav", b, log)


def measure_loudness(path: Path, log=None) -> dict | None:
    err = run_ffmpeg_analysis(["-i", str(path), "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                               "-f", "null", "-"], log, "measuring loudness")
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S)
    return json.loads(m.group(0)) if m else None


def normalize(src: Path, dst: Path, b: dict, log) -> Path:
    target, tp = float(b.get("loudness_lufs", -14)), float(b.get("true_peak_db", -1.5))
    st = measure_loudness(src, log)
    if not st or st["input_i"] in ("-inf", "inf") or float(st["input_i"]) < -70:
        log.debug("audio is silent - loudness normalisation skipped")
        shutil.copy(src, dst)
        return dst
    af = (f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
          f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:"
          f"linear=true,aresample=48000")
    run_ffmpeg(["-i", str(src), "-af", af, "-c:a", "pcm_f32le", str(dst)], log, desc="normalising loudness")
    log.debug(f"loudness before: {st['input_i']} LUFS, target {target}")
    return dst
