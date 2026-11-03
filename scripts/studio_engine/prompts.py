"""Scene prompts for Higgsfield (manual workflow) + shot list + importing the downloaded clips.

Every shot has an id like s03-a. Save the generated clip as  s03-a.mp4  (or keep the shot id
anywhere in the file name) and run  studio import-clips  - it is copied to
assets/video/<slug>/s03-a.mp4 where the editing timeline expects it.
Nothing here generates video or spends credits.
"""
from __future__ import annotations

import csv
import re
import shutil
import time
from pathlib import Path

from sfl_engine.util import IMAGE_EXT, VIDEO_EXT, SFLError, probe, rel, unique_output

from .common import Production, fval
from .research import load_research
from .script import load_script, studio_cfg

SHOT_RE = re.compile(r"(s\d{2})[-_ ]?(photo|[a-z])(?:[-_ ]?(v))?(?![a-z0-9])", re.I)


def shots(prod: Production):
    """All shots in script order, with the scenes used by Shorts flagged (they get a 9:16 version)."""
    s = load_script(prod)
    short_scenes = {u for sh in s.get("shorts") or [] for u in sh.get("use_scenes") or []}
    out = []
    for i, sc in enumerate(s.get("scenes") or [], 1):
        for sh in sc.get("shots") or []:
            out.append({**sh, "scene": sc["id"], "scene_no": i, "role": sc.get("role"), "rank": sc.get("rank"),
                        "for_shorts": sc["id"] in short_scenes})
    return out


def shot_file(prod: Production, shot: dict, vertical=False):
    """Where the imported file for a shot lives (first existing match), or None."""
    if shot.get("type") == "product_photo":
        base = prod.image_dir
        stem = shot.get("product") or shot["id"]
        exts = IMAGE_EXT
    else:
        base = prod.video_dir
        stem = shot["id"] + ("-v" if vertical else "")
        exts = VIDEO_EXT
    for e in sorted(exts):
        f = base / f"{stem}{e}"
        if f.exists():
            return f
    return None


def write_prompts(prod: Production, log):
    prod.require("script", why="Write and check the script first.")
    cfg = studio_cfg()
    vs = cfg["visual_style"]
    data = load_research(prod)
    names = {p["id"]: fval(p["name"]) for p in data.get("products", [])}
    all_shots = shots(prod)
    rows = []
    L = [f"# Scene prompts — {prod.title}", "",
         "**Manual Higgsfield workflow.** Nothing here has been generated. For each shot: paste the prompt into "
         "Higgsfield, generate, download, and name the file exactly as **Save as** (or keep the shot id, e.g. "
         "`s03-a`, anywhere in the file name). Then run:", "",
         f"```bash\npython scripts/studio.py import-clips {prod.slug} \"PATH/TO/YOUR/DOWNLOADS\"\n```", "",
         "Rules: AI clips are **generic b-roll** (hands, kitchen, the task). They must not pretend to show the exact "
         "product: the real product is identified with the product photo shot. If YouTube asks, tick *altered or "
         "synthetic content* for realistic AI scenes.", "",
         f"Style added to every prompt: *{vs['suffix']}*  ", f"Avoid: *{vs['avoid']}*", ""]
    current = None
    for sh in all_shots:
        if sh["scene"] != current:
            current = sh["scene"]
            label = {"hook": "Hook", "wrapup": "Wrap-up"}.get(sh["role"], f"#{sh['rank']} {names.get(sh.get('product'), '')}")
            L += [f"## Scene {sh['scene_no']} — {sh['scene']} · {label}", ""]
        if sh.get("type") == "product_photo":
            target = f"assets/images/{prod.slug}/{sh.get('product')}.jpg"
            have = shot_file(prod, sh)
            L += [f"### `{sh['id']}` — real product photo", "",
                  f"- Save as: `{target}` (JPG or PNG, at least 1500 px; a transparent PNG cut-out works too)",
                  f"- {sh.get('prompt', '')}", f"- Status: {'✅ imported: ' + rel(have) if have else '⏳ not provided yet'}",
                  ""]
            rows.append({"shot_id": sh["id"], "scene": sh["scene"], "scene_no": sh["scene_no"], "type": "product_photo",
                         "product": names.get(sh.get("product"), ""), "aspect": "any", "seconds": "",
                         "save_as": target, "prompt": sh.get("prompt", ""),
                         "status": "imported" if have else "pending"})
            continue
        cam = f" Camera: {sh['camera']}." if sh.get("camera") else ""
        full = f"{sh['prompt'].rstrip('.')}.{cam} {vs['suffix']}"
        versions = [("16:9", "", "long video")]
        if sh["for_shorts"]:
            versions.append(("9:16", "-v", "Short (vertical)"))
        L += [f"### `{sh['id']}` — AI b-roll", ""]
        for aspect, suf, use in versions:
            have = shot_file(prod, sh, vertical=bool(suf))
            save = f"{sh['id']}{suf}.mp4"
            L += [f"**{use}** — aspect **{aspect}**, {vs.get('clip_seconds', 5)} s, save as `{save}` · "
                  f"{'✅ imported: ' + rel(have) if have else '⏳ not generated/imported'}", "",
                  "```text", full, "```", ""]
            rows.append({"shot_id": sh["id"] + suf, "scene": sh["scene"], "scene_no": sh["scene_no"], "type": "ai_broll",
                         "product": names.get(sh.get("product"), ""), "aspect": aspect,
                         "seconds": vs.get("clip_seconds", 5), "save_as": f"assets/video/{prod.slug}/{save}",
                         "prompt": full, "status": "imported" if have else "pending"})
        L += [f"*Negative / avoid:* {vs['avoid']}", ""]
    prod.p("prompts", "higgsfield-prompts.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(prod.p("prompts", "shotlist.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["shot_id"])
        w.writeheader()
        w.writerows(rows)
    pending = sum(1 for r in rows if r["status"] == "pending")
    log.info(f"Prompts: {rel(prod.p('prompts', 'higgsfield-prompts.md'))}  ({len(rows)} items, {pending} still needed)")
    log.info(f"Shot list: {rel(prod.p('prompts', 'shotlist.csv'))}")
    return rows


def import_clips(prod: Production, folder, log):
    """Copy (never move) files whose name contains a shot id into the right asset folder."""
    src = Path(folder).expanduser()
    if not src.is_dir():
        raise SFLError(f"Folder not found: {src}")
    known = {sh["id"]: sh for sh in shots(prod)}
    files = sorted(p for p in src.rglob("*") if p.suffix.lower() in VIDEO_EXT | IMAGE_EXT)
    if not files:
        raise SFLError(f"No video or image files in {src}")
    prod.video_dir.mkdir(parents=True, exist_ok=True)
    prod.image_dir.mkdir(parents=True, exist_ok=True)
    man = prod.video_dir / "manifest.csv"
    new = not man.exists()
    done, unmatched = [], []
    with open(man, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["imported", "original_file", "new_file", "shot_id", "width", "height", "seconds", "notes"])
        for f in files:
            m = SHOT_RE.search(f.stem.lower())
            sid = f"{m.group(1)}-{m.group(2)}" if m else None
            if not sid or sid not in known:
                unmatched.append(f.name)
                continue
            sh = known[sid]
            is_img = f.suffix.lower() in IMAGE_EXT
            if sh.get("type") == "product_photo":
                if not is_img:
                    unmatched.append(f.name + " (photo shot needs an image)")
                    continue
                dest = prod.image_dir / f"{sh.get('product')}{f.suffix.lower()}"
            else:
                if is_img:
                    unmatched.append(f.name + " (b-roll shot needs a video)")
                    continue
                dest = prod.video_dir / f"{sid}{'-v' if m.group(3) else ''}{f.suffix.lower()}"
            existed = dest.exists()
            target = unique_output(dest)
            shutil.copy2(f, target)
            notes = []
            try:
                info = probe(target)
                if info.get("height") and min(info["width"], info["height"]) < 1080:
                    notes.append("below 1080p")
                dims = (info.get("width"), info.get("height"), info.get("duration"))
            except SFLError as e:
                dims = ("", "", "")
                notes.append(f"UNREADABLE: {e}")
            if existed:
                notes.append(f"{dest.name} already existed - saved as {target.name}; delete the old file to use it")
            w.writerow([time.strftime("%Y-%m-%d"), f.name, target.name, sid, dims[0], dims[1],
                        f"{dims[2]:.2f}" if dims[2] else "", "; ".join(notes)])
            done.append(target)
            log.info(f"   {f.name}  ->  {rel(target)}  {'; '.join(notes)}")
    if unmatched:
        log.info("\n   Not imported (no known shot id in the file name - rename e.g. to s03-a.mp4):")
        for u in unmatched:
            log.info(f"     - {u}")
    log.info(f"\nCopied {len(done)} file(s). Your original files were not changed.")
    return done, unmatched


def write_visual_plan(prod: Production, log, script: dict | None = None, out_name: str = "visual-plan.md"):
    """Scene-by-scene visual production plan (shots, camera, overlays, timing, transitions).
    script/out_name let a review proposal be planned without touching the approved script."""
    from .script import est_seconds, load_script

    prod.require("script", why="Write and check the script first.")
    s = script or load_script(prod)
    wpm = float(s.get("words_per_minute") or 155)
    data = load_research(prod)
    names = {p["id"]: fval(p["name"]) for p in data.get("products", [])}
    total = 0.0
    L = [f"# Visual production plan — {prod.title}", "",
         "Generated from `script/script.yaml`. Durations are estimates from the narration "
         f"({wpm:.0f} words/min); the editor fits the real voice-over automatically. Clips shorter than a scene "
         "repeat in order (fill: cycle); longer ones are trimmed.", "",
         "**Sources of visuals:** 🎬 AI b-roll (Higgsfield, generic — must not imitate the exact product) · "
         "📷 real product photo (your own photo or a manufacturer image you are licensed to use). "
         "Never use footage from reference channels or images from Amazon listings without permission.", "",
         "Automatic in every video (config/brand.yaml): brand intro sting after the hook, 12 s end-screen outro, "
         "watermark, subtitles, background music ducking, whoosh on transitions, pop on badges.", ""]
    for i, sc in enumerate(s.get("scenes") or [], 1):
        sec = est_seconds(sc.get("narration", ""), wpm)
        total += sec
        title = {"hook": "Hook", "setup": "Honesty & affiliate note", "wrapup": "Wrap-up & call to action"}.get(
            sc.get("role"), f"#{sc.get('rank')} {names.get(sc.get('product'), '')}")
        L += [f"## Scene {i} — `{sc['id']}` · {title}", "",
              f"- **Approx. duration:** {sec:.0f} s of narration"
              + (" (+0.5 s pauses)" if sc.get("role") == "product" else ""),
              f"- **Transition into this scene:** {sc.get('transition') or 'brand default (fade)'}"]
        os_ = sc.get("on_screen") or {}
        ov = []
        if os_.get("title"):
            ov.append(f"title \"{os_['title']}\" (0.4 s → 3.9 s)")
        if os_.get("badge"):
            ov.append(f"badge {os_['badge']} (whole scene)")
        if os_.get("lower_third"):
            ov.append(f"lower third \"{os_['lower_third']}\" / \"{os_.get('lower_third_sub', '')}\" (0.8 s → 5.3 s)")
        if os_.get("callout"):
            ov.append(f"callout \"{os_['callout']}\" (from 6 s)")
        if os_.get("cta"):
            ov.append(f"CTA \"{os_['cta']}\" (from 0.5 s to the end)")
        L.append("- **Text overlays:** " + ("; ".join(ov) if ov else "subtitles only"))
        L += ["", "| Shot | Source | Camera / angle | ~Seconds | What we see |", "|---|---|---|---|---|"]
        shot_total = 0
        for sh in sc.get("shots") or []:
            src = {"product_photo": f"📷 product photo ({sh.get('motion', 'zoom_in')}, crop: {sh.get('crop', 'full')})",
                   "stock": "🎞️ free-licence stock", "graphic": "🔤 graphic (made by the editor)"}.get(
                sh.get("type"), "🎬 AI b-roll")
            have = shot_file(prod, sh)
            shot_total += float(sh.get("seconds") or 0)
            what = {"product_photo": f"{names.get(sh.get('product'), '')} — real product photo",
                    "stock": f"search: \"{sh.get('search', '')}\"",
                    "graphic": f"{sh.get('graphic', '')}: {sh.get('text', '')}"}.get(sh.get("type"), sh.get("prompt", ""))
            L.append(f"| `{sh['id']}`{' ✅' if have else ''} | {src} | {sh.get('camera', '—')} | {sh.get('seconds', '—')} | {what} |")
        if shot_total and shot_total < sec * 0.6:
            L.append(f"\n*Shots cover ~{shot_total:.0f} s of ~{sec:.0f} s — the clips will repeat; adding 1–2 more "
                     "shots would make this scene feel richer.*")
        if sc.get("needs_verification"):
            L += ["", "**Verify before publishing:** " + "; ".join(sc["needs_verification"])]
        L.append("")
    L += [f"**Estimated narration total:** {total / 60:.1f} min (+ intro sting 2.6 s, outro 12 s, transitions).", "",
          "Higgsfield prompts for every 🎬 shot: `prompts/higgsfield-prompts.md` · shot list: `prompts/shotlist.csv`."]
    out = prod.dir / "production" / out_name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    log.info(f"Visual plan: {rel(out)}")
    return out
