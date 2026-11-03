"""Helper tools: sound effects, test media, clip import, thumbnails, new projects, doctor."""
from __future__ import annotations

import csv
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .util import (AUDIO_EXT, IMAGE_EXT, ROOT, VIDEO_EXT, SFLError, ffpath, find_tool, probe, rel, resolve,
                   run_ffmpeg, slugify, unique_output)

# --------------------------------------------------------------------------- sound effects
# All sounds are synthesised from maths (no samples) -> 100 % original, copyright-free.
SFX = {
    "whoosh": ("anoisesrc=color=pink:r=48000:a=0.9:d=0.7",
               "bandpass=f=1400:width_type=o:w=2.5,volume='if(lt(t,0.32),pow(t/0.32,2),max(0,(0.7-t)/0.38))':eval=frame"),
    "pop": ("aevalsrc='0.9*sin(2*PI*(260+700*exp(-t*45))*t)*exp(-t*28)':s=48000:d=0.2", None),
    "ding": ("aevalsrc='0.45*(sin(2*PI*1318.5*t)+0.45*sin(2*PI*2637*t)+0.2*sin(2*PI*3955*t))*exp(-t*4.5)':s=48000:d=1.4", None),
    "click": ("aevalsrc='0.8*sin(2*PI*2100*t)*exp(-t*260)':s=48000:d=0.06", None),
    "riser": ("aevalsrc='0.22*sin(2*PI*(180*t+170*t*t))*pow(t/1.6,1.5)+0.12*sin(2*PI*(360*t+340*t*t))*pow(t/1.6,2)':s=48000:d=1.6",
              "afade=t=out:st=1.45:d=0.15"),
    "swipe": ("anoisesrc=color=white:r=48000:a=0.6:d=0.35",
              "highpass=f=2500,volume='if(lt(t,0.12),t/0.12,max(0,(0.35-t)/0.23))':eval=frame"),
}


def make_sfx(log, force=False):
    out = ROOT / "assets" / "sound-effects" / "generated"
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for name, (src, af) in SFX.items():
        dst = out / f"{name}.wav"
        if dst.exists() and not force:
            log.info(f"   exists, kept: {rel(dst)}")
            continue
        args = ["-f", "lavfi", "-i", src]
        if af:
            args += ["-af", af]
        args += ["-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(dst)]
        run_ffmpeg(args, log, desc=f"sound effect {name}")
        made.append(dst)
        log.info(f"   created {rel(dst)}")
    return made


# --------------------------------------------------------------------------- test media
def make_test_media(log):
    """Synthetic placeholder media so the pipeline can be tested without real footage.
    Every file is clearly labelled TEST PLACEHOLDER - none of it shows a real product."""
    from PIL import Image, ImageDraw, ImageFont

    d = ROOT / "samples" / "test-media"
    d.mkdir(parents=True, exist_ok=True)
    font_file = str(ROOT / "assets" / "fonts" / "Inter-ExtraBold.otf")
    font = ffpath(font_file)  # escaped for FFmpeg filters (Windows drive letters contain ':')
    lbl = lambda t, y="h-120", size=56: (f"drawtext=fontfile='{font}':text='{t}':fontcolor=white:fontsize={size}:"
                                          f"x=(w-text_w)/2:y={y}:box=1:boxcolor=black@0.55:boxborderw=18")
    jobs = {
        # object (with its label) on the LEFT third, moving: auto-reframe for Shorts should follow it
        "clip_a_left_object.mp4": (["-f", "lavfi", "-i", "gradients=s=1920x1080:c0=0x1E293B:c1=0x334155:speed=0.01:r=30:d=8"],
            "drawbox=x=300+90*sin(t):y=300:w=420:h=420:color=0xF59E0B@1:t=fill,"
            "drawbox=x=350+90*sin(t):y=350:w=320:h=320:color=0xFFFFFF@0.9:t=fill,"
            f"drawtext=fontfile='{font}':text='TEST PLACEHOLDER A':fontcolor=white:fontsize=40:"
            "x=510+90*sin(t)-text_w/2:y=760:box=1:boxcolor=black@0.55:boxborderw=12,"
            f"drawtext=fontfile='{font}':text='not real product footage':fontcolor=white:fontsize=26:"
            "x=510+90*sin(t)-text_w/2:y=830", None),
        "clip_b_with_sound.mp4": (["-f", "lavfi", "-i", "testsrc2=s=1920x1080:r=30:d=6",
                                   "-f", "lavfi", "-i", "sine=f=330:d=6:r=48000"],
            "eq=saturation=0.6," + lbl("TEST PLACEHOLDER CLIP B (has sound)"), "a"),
        "clip_c_vertical.mp4": (["-f", "lavfi", "-i", "gradients=s=1080x1920:c0=0x0F766E:c1=0x134E4A:speed=0.02:r=30:d=5"],
            "drawbox=x=290:y=700+60*sin(2*t):w=500:h=500:color=0xE2E8F0@1:t=fill,"
            + lbl("VERTICAL PLACEHOLDER", "h-260", 54), None),
        "clip_d_very_short.mp4": (["-f", "lavfi", "-i", "gradients=s=1920x1080:c0=0x3B0764:c1=0x1E1B4B:speed=0.05:r=30:d=2"],
            lbl("TEST PLACEHOLDER CLIP D (2 seconds)", "(h-text_h)/2", 60), None),
    }
    for name, (inp, vf, audio) in jobs.items():
        dst = d / name
        if dst.exists():
            continue
        args = inp + ["-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p"]
        args += (["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"] if audio else ["-an"])
        run_ffmpeg(args + [str(dst)], log, desc=f"test clip {name}")
        log.info(f"   created {rel(dst)}")

    f_big = ImageFont.truetype(font_file, 90)
    f_small = ImageFont.truetype(font_file, 46)
    img1 = d / "image_1_square.jpg"
    if not img1.exists():
        im = Image.new("RGB", (2000, 2000), (226, 232, 240))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((600, 500, 1400, 1450), 60, fill=(20, 184, 166))
        dr.ellipse((800, 700, 1200, 1100), fill=(255, 255, 255))
        dr.text((1000, 1650), "TEST PLACEHOLDER IMAGE", font=f_big, fill=(15, 23, 42), anchor="mm")
        dr.text((1000, 1760), "not a real product photo", font=f_small, fill=(71, 85, 105), anchor="mm")
        im.save(img1, quality=92)
        log.info(f"   created {rel(img1)}")
    img2 = d / "image_2_cutout.png"
    if not img2.exists():
        im = Image.new("RGBA", (1200, 1200), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle((350, 200, 850, 900), 80, fill=(245, 158, 11, 255))
        dr.rectangle((550, 120, 650, 220), fill=(30, 41, 59, 255))
        dr.text((600, 1000), "PLACEHOLDER CUT-OUT", font=f_small, fill=(15, 23, 42, 255), anchor="mm")
        im.save(img2)
        log.info(f"   created {rel(img2)}")

    # pseudo-speech: a buzzing tone with syllable rhythm and pauses (NOT real speech)
    speech = ("aevalsrc='0.32*(sin(2*PI*140*t)+0.6*sin(2*PI*280*t)+0.35*sin(2*PI*560*t))"
              "*(0.55+0.45*sin(2*PI*4.3*t))*gt(sin(2*PI*0.37*t+1),-0.75)':s=48000:d={d}")
    for i, dur in enumerate([5.5, 8.0, 7.0, 4.5], 1):
        dst = d / f"voice_{i:02d}_placeholder.wav"
        if not dst.exists():
            run_ffmpeg(["-f", "lavfi", "-i", speech.format(d=dur), "-af", "lowpass=f=3000,afade=t=out:st="
                        f"{dur - 0.2}:d=0.2", "-ac", "1", "-c:a", "pcm_s16le", str(dst)], log, desc="placeholder voice")
            log.info(f"   created {rel(dst)}")
    srt = d / "voice_02_placeholder.srt"
    if not srt.exists():
        srt.write_text("1\n00:00:00,000 --> 00:00:02,600\nThis subtitle comes from an SRT file.\n\n"
                       "2\n00:00:02,600 --> 00:00:05,200\nTimings in SRT files are exact.\n\n"
                       "3\n00:00:05,200 --> 00:00:08,000\nThat is the best way to get perfect sync.\n",
                       encoding="utf-8")
    music = d / "music_placeholder_generated.wav"
    if not music.exists():
        ch = lambda fs: "+".join(f"sin(2*PI*{f}*t)" for f in fs)
        expr = (f"0.08*if(lt(mod(t,8),4),{ch([261.6, 329.6, 392.0, 493.9])},{ch([220.0, 261.6, 329.6, 392.0])})"
                f"*(0.75+0.25*sin(2*PI*0.25*t))")
        run_ffmpeg(["-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d=40", "-af", "lowpass=f=1800,aecho=0.6:0.5:180:0.3",
                    "-ac", "2", "-c:a", "pcm_s16le", str(music)], log, desc="placeholder music")
        log.info(f"   created {rel(music)}")
    # one long "master" voice-over (voices 1-4 joined) + its SRT, to test the single-file workflow
    full = d / "voiceover_full_placeholder.wav"
    if not full.exists():
        run_ffmpeg([a for i in range(1, 5) for a in ("-i", str(d / f"voice_{i:02d}_placeholder.wav"))]
                   + ["-filter_complex", "[0:a][1:a][2:a][3:a]concat=n=4:v=0:a=1[a]", "-map", "[a]",
                      "-c:a", "pcm_s16le", str(full)], log, desc="placeholder master voice-over")
        log.info(f"   created {rel(full)}")
    fsrt = d / "voiceover_full_placeholder.srt"
    if not fsrt.exists():
        lines = ["Part one of the master voice-over.", "Part two comes from the same file.",
                 "Part three keeps the same timing.", "Part four ends the test."]
        starts = [0.0, 5.5, 13.5, 20.5, 25.0]
        from .subtitles import write_srt
        write_srt([(starts[i], starts[i + 1] - 0.1, t) for i, t in enumerate(lines)], fsrt)
    (d / "README.txt").write_text(
        "TEST PLACEHOLDER MEDIA - generated by 'python scripts/sfl.py make-test-media'.\n"
        "Nothing here shows a real product or a real voice. It only exists to test the editing system.\n"
        "Never publish videos made from these files.\n", encoding="utf-8")
    return d


# --------------------------------------------------------------------------- import clips
def import_clips(src_folder, dest_name, log, prefix=""):
    """Copy (never move) downloaded clips into assets/, with clean names and a manifest."""
    src = Path(src_folder).expanduser()
    if not src.is_dir():
        raise SFLError(f"Folder not found: {src}")
    dest = ROOT / "assets" / "video" / slugify(dest_name)
    dest.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.rglob("*") if p.suffix.lower() in VIDEO_EXT | IMAGE_EXT)
    if not files:
        raise SFLError(f"No video or image files found in {src}")
    man_path = dest / "manifest.csv"
    new_manifest = not man_path.exists()
    rows = []
    with open(man_path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new_manifest:
            w.writerow(["imported", "original_file", "new_file", "width", "height", "aspect", "fps", "seconds",
                        "has_audio", "notes"])
        for i, f in enumerate(files, 1):
            base = slugify(f.stem)[:50]
            name = f"{slugify(prefix) + '_' if prefix else ''}{base}{f.suffix.lower()}"
            target = unique_output(dest / name)
            shutil.copy2(f, target)
            notes = []
            try:
                info = probe(target)
                ar = info["width"] / info["height"]
                aspect = "16:9" if abs(ar - 16 / 9) < 0.03 else "9:16" if abs(ar - 9 / 16) < 0.03 else \
                    "1:1" if abs(ar - 1) < 0.03 else f"{ar:.2f}:1"
                if min(info["width"], info["height"]) < 1080:
                    notes.append("below 1080p - consider upscaling")
                if info["duration"] and info["duration"] < 3:
                    notes.append("very short")
                row = [time.strftime("%Y-%m-%d"), f.name, target.name, info["width"], info["height"], aspect,
                       f"{info['fps']:.2f}" if info["fps"] else "", f"{info['duration']:.2f}" if info["duration"] else "",
                       info["has_audio"], "; ".join(notes)]
            except SFLError as e:
                row = [time.strftime("%Y-%m-%d"), f.name, target.name, "", "", "", "", "", "", f"UNREADABLE: {e}"]
            w.writerow(row)
            rows.append(row)
            log.info(f"   {f.name}  ->  {rel(target)}  {row[3]}x{row[4]} {row[7]}s {row[9]}")
    log.info(f"\nCopied {len(rows)} file(s). Originals were not changed. Manifest: {rel(man_path)}")
    log.info("Paste into a timeline scene, e.g.:\n    clips:")
    for r in rows[:3]:
        log.info(f"      - source: {rel(dest / r[2])}")
    return rows


# --------------------------------------------------------------------------- thumbnails
def make_thumbnail(text, sub, log, image=None, video=None, at=None, out_name=None, badge=None, brand=None,
                   out_path=None):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    from .config import load_brand
    from .util import hex_rgb

    brand = brand or load_brand()
    W, H = 1280, 720
    fonts = resolve(brand["fonts"]["folder"])
    col = {k: hex_rgb(v) for k, v in brand["colors"].items()}
    tmp = None
    if video:
        tmp = ROOT / "temp" / "thumb_frame.png"
        tmp.parent.mkdir(exist_ok=True)
        run_ffmpeg(["-ss", str(at or 1), "-i", str(resolve(video)), "-frames:v", "1", str(tmp)], log, desc="grab frame")
        image = tmp
    if image:
        bg = Image.open(resolve(image)).convert("RGB")
        s = max(W / bg.width, H / bg.height)
        bg = bg.resize((int(bg.width * s + 1), int(bg.height * s + 1)), Image.LANCZOS)
        l, t = (bg.width - W) // 2, (bg.height - H) // 2
        bg = bg.crop((l, t, l + W, t + H))
    else:
        bg = Image.new("RGB", (W, H), col["dark"])
    # darken the left side so text stays readable
    shade = Image.new("L", (W, H))
    sd = ImageDraw.Draw(shade)
    for x in range(W):
        sd.line([(x, 0), (x, H)], fill=int(200 * max(0.0, 1 - x / (W * 0.75))))
    bg = Image.composite(Image.new("RGB", (W, H), col["dark"]), bg, shade)
    dr = ImageDraw.Draw(bg)
    fh = str(fonts / brand["fonts"]["caption"]["file"])
    size = 112
    lines = str(text).upper().split("\\n") if "\\n" in str(text) else _wrap(str(text).upper(), fh, size, W * 0.62)
    while len(lines) > 3 or max(ImageFont.truetype(fh, size).getlength(ln) for ln in lines) > W * 0.66:
        size -= 6
        lines = _wrap(str(text).upper(), fh, size, W * 0.62)
    f = ImageFont.truetype(fh, size)
    y = (H - len(lines) * size * 1.05 - (70 if sub else 0)) / 2
    x = 64
    for i, ln in enumerate(lines):
        fill = col["secondary"] if i == len(lines) - 1 and len(lines) > 1 else col["light"]
        dr.text((x, y), ln, font=f, fill=fill, stroke_width=6, stroke_fill=col["dark"])
        y += size * 1.05
    dr.rounded_rectangle((x, y + 14, x + 160, y + 26), 6, fill=col["primary"])
    if sub:
        fs = ImageFont.truetype(str(fonts / brand["fonts"]["heading"]["file"]), 44)
        dr.text((x, y + 44), str(sub), font=fs, fill=col["light"], stroke_width=3, stroke_fill=col["dark"])
    if badge:
        fb = ImageFont.truetype(fh, 54)
        bw = fb.getlength(str(badge)) + 56
        dr.rounded_rectangle((W - bw - 40, 40, W - 40, 130), 22, fill=col["primary"])
        dr.text((W - 40 - bw / 2, 85), str(badge), font=fb, fill=col["dark"], anchor="mm")
    out = Path(out_path) if out_path else unique_output(ROOT / "thumbnails" / f"{slugify(out_name or text)}.jpg")
    out.parent.mkdir(exist_ok=True)
    bg.save(out, quality=92)
    if tmp and tmp.exists():
        tmp.unlink()
    log.info(f"Thumbnail saved: {rel(out)} (1280x720)")
    return out


def _wrap(text, font_path, size, max_w):
    from PIL import ImageFont
    f = ImageFont.truetype(font_path, size)
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if cur and f.getlength(t) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def extract_frames(video, count, log):
    video = resolve(video)
    info = probe(video)
    out = ROOT / "thumbnails" / "frames" / slugify(video.stem)
    out.mkdir(parents=True, exist_ok=True)
    dur = info["duration"] or 1
    for i in range(count):
        t = dur * (i + 0.5) / count
        dst = out / f"frame_{i + 1:02d}_{t:06.1f}s.jpg"
        run_ffmpeg(["-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(dst)], log, desc="frame")
    log.info(f"Saved {count} frames to {rel(out)} - pick one for your thumbnail.")


# --------------------------------------------------------------------------- new project
def new_project(title, n_products, log):
    slug = slugify(title)[:40]
    dst = ROOT / "config" / "timelines" / f"{slug}.yaml"
    if dst.exists():
        raise SFLError(f"{rel(dst)} already exists - choose another title or edit that file.")
    L = [f"# Timeline for: {title}", "# Edit this file, then run:  python scripts/sfl.py check " + rel(dst),
         "", "project:", f'  title: "{title}"', f"  output: {slug}", "  format: long", "",
         "audio:", f"  music: assets/music/YOUR-MUSIC.mp3", '  music_license: "WRITE WHERE THE MUSIC IS FROM"', "",
         "subtitles:", "  mode: auto", "", "intro:", "  position: after_first_scene", "", "scenes:",
         "  - id: hook", f"    voice: assets/audio/{slug}/00_hook.mp3", "    narration: >", "      [Write your hook here]",
         "    clips:", f"      - source: assets/video/{slug}/hook_a.mp4", f"      - source: assets/video/{slug}/hook_b.mp4",
         "    overlays:", "      - type: title", f'        text: "{title}"', ""]
    for i in range(n_products, 0, -1):
        L += [f"  - id: p{i:02d}", f"    voice: assets/audio/{slug}/{i:02d}.mp3", "    narration: >",
              f"      [Narration for product {i}]", "    clips:", f"      - source: assets/video/{slug}/p{i:02d}_a.mp4",
              f"      - source: assets/video/{slug}/p{i:02d}_b.mp4", f"      - source: assets/images/{slug}/p{i:02d}.jpg",
              "    overlays:", "      - type: badge", f'        text: "#{i}"', "      - type: lower_third",
              f'        text: "[Product {i} name]"', '        subtitle: "[Best for ...]"', ""]
    L += ["  - id: wrapup", f"    voice: assets/audio/{slug}/99_wrapup.mp3", "    narration: >",
          "      [Short summary + call to action]", "    clips:", f"      - source: assets/video/{slug}/wrapup.mp4",
          "    overlays:", "      - type: cta", '        text: "Links in the description"', ""]
    dst.write_text("\n".join(L), encoding="utf-8")
    for sub in (f"assets/video/{slug}", f"assets/audio/{slug}", f"assets/images/{slug}"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    log.info(f"Created {rel(dst)} and media folders assets/video/{slug}/, assets/audio/{slug}/, assets/images/{slug}/")
    log.info(f"Next: put your files there, edit the timeline, then run:\n  python scripts/sfl.py check {rel(dst)}")
    return dst


# --------------------------------------------------------------------------- doctor
def doctor(log):
    ok = True
    log.info(f"Operating system : {platform.system()} {platform.release()} ({platform.machine()})")
    log.info(f"Python           : {sys.version.split()[0]} {'OK' if sys.version_info >= (3, 9) else 'TOO OLD (need 3.9+)'}")
    for tool in ("ffmpeg", "ffprobe"):
        try:
            p = find_tool(tool)
            v = subprocess.run([p, "-version"], capture_output=True, text=True).stdout.split("\n")[0]
            log.info(f"{tool:<17}: {v[:70]}")
        except SFLError:
            log.info(f"{tool:<17}: MISSING - see docs/INSTALL.md")
            ok = False
    try:
        fl = subprocess.run([find_tool("ffmpeg"), "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        enc = subprocess.run([find_tool("ffmpeg"), "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
        need = {"ass (libass)": " ass ", "xfade": " xfade ", "loudnorm": " loudnorm ", "zoompan": " zoompan ",
                "sidechaincompress": " sidechaincompress ", "gradients": " gradients ", "blackdetect": " blackdetect "}
        for k, s in need.items():
            has = s in fl
            ok &= has
            log.info(f"  filter {k:<20}: {'OK' if has else 'MISSING - install a full FFmpeg build'}")
        has264 = "libx264" in enc
        ok &= has264
        log.info(f"  encoder libx264        : {'OK' if has264 else 'MISSING - install a full FFmpeg build'}")
    except SFLError:
        pass
    for mod, why in (("yaml", "PyYAML (required)"), ("PIL", "Pillow (required)"), ("numpy", "numpy (required)"),
                     ("faster_whisper", "faster-whisper (optional: exact auto-subtitles)")):
        try:
            __import__(mod)
            log.info(f"  python {why:<44}: OK")
        except ImportError:
            req = "required" in why
            ok &= not req
            log.info(f"  python {why:<44}: {'MISSING - run: pip install -r requirements.txt' if req else 'not installed (optional)'}")
    node = shutil.which("node")
    log.info(f"Node.js (optional): {subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip() if node else 'not installed (not needed)'}")
    du = shutil.disk_usage(ROOT)
    log.info(f"Free disk space   : {du.free / 1e9:.1f} GB {'(low! keep 20 GB+ free)' if du.free < 20e9 else ''}")
    fonts = list((ROOT / "assets" / "fonts").glob("*.otf"))
    log.info(f"Brand fonts       : {len(fonts)} font files in assets/fonts")
    log.info("\nRESULT: " + ("everything needed is installed." if ok else "something is missing - see above."))
    return ok
