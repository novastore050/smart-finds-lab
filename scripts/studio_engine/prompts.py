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
        full = f"{sh['prompt'].rstrip('.')}. {vs['suffix']}"
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
