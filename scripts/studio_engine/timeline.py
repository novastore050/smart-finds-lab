"""Script + imported assets  ->  editing timeline (edit/timeline.yaml) and Shorts file (edit/shorts.yaml).

The files produced are ordinary timelines for the existing FFmpeg editor (scripts/sfl.py),
so they can be checked, edited by hand and rendered exactly like before.
"""
from __future__ import annotations

import hashlib

from sfl_engine.config import GRAPHIC_KINDS, MOTIONS
from sfl_engine.util import ROOT, rel

from .common import Production, fval, save_yaml
from .prompts import shot_file
from .research import load_research
from .script import dedicated_shorts, est_seconds, load_script
from .voice import scene_audio

# product-photo "crop" in the script -> how the editor frames the photo
#   full  : whole product visible (contain, no crop)
#   other : a closer detail crop (cover + base zoom) around focus_x/focus_y (default centre)
DETAIL_ZOOM = 1.35


def photo_clip(f, sh: dict) -> dict:
    motion = sh.get("motion") if sh.get("motion") in MOTIONS else "zoom_in"
    crop = str(sh.get("crop") or "full")
    clip = {"source": rel(f), "motion": motion, "duration": float(sh.get("seconds") or 4)}
    if crop == "full":
        clip["fit"] = "contain"
    else:
        clip.update({"fit": "cover", "zoom": float(sh.get("zoom") or DETAIL_ZOOM),
                     "focus_x": float(sh.get("focus_x", 0.5)), "focus_y": float(sh.get("focus_y", 0.5))})
    return clip


def graphic_clip(sh: dict) -> dict:
    kind = sh.get("graphic") if sh.get("graphic") in GRAPHIC_KINDS else "note"
    return {"type": "card", "background": "gradient", "duration": float(sh.get("seconds") or 4),
            "graphic": kind, "text": str(sh.get("text") or "")}


def _scene_entry(prod: Production, sc: dict, wpm: float, missing: list, placeholders: bool, vertical=False):
    e = {"id": sc["id"], "narration": " ".join(str(sc.get("narration", "")).split())}
    if sc.get("transition") and not vertical:  # Shorts use their own quick transitions
        e["transition"] = sc["transition"]
    audio = scene_audio(prod, sc["id"])
    if audio:
        e["voice"] = rel(audio)
        srt = prod.p("voice", f"{sc['id']}.srt")
        if srt.exists():
            e["subtitles"] = rel(srt)
    else:
        # no voice yet: give the scene its estimated length so timing/chapters can be previewed
        e["duration"] = max(3.0, est_seconds(sc.get("narration", ""), wpm) + 1.0)
        missing.append(f"voice {sc['id']}  ->  {rel(prod.p('voice', sc['id'] + '.mp3'))}")
    clips = []
    for sh in sc.get("shots") or []:
        if sh.get("type") == "graphic":
            clips.append(graphic_clip(sh))  # made by the editor - never "missing"
            continue
        if sh.get("type") == "product_photo":
            f = shot_file(prod, sh)
            if f:
                clips.append(photo_clip(f, sh))
            else:
                missing.append(f"photo {sh['id']}  ->  assets/images/{prod.slug}/{sh.get('product')}.jpg")
            continue
        f = (shot_file(prod, sh, vertical=True) if vertical else None) or shot_file(prod, sh)
        if f:
            clips.append({"source": rel(f)})
        else:
            missing.append(f"clip {sh['id']}  ->  assets/video/{prod.slug}/{sh['id']}.mp4")
            if not placeholders:
                clips.append({"source": f"assets/video/{prod.slug}/{sh['id']}.mp4"})
    if not clips:  # draft preview without media: a branded card instead
        e["type"] = "card"
        e["title"] = (sc.get("on_screen") or {}).get("lower_third") or (sc.get("on_screen") or {}).get("title") or ""
        e["subtitle"] = "[media missing - preview]"
        e["background"] = "gradient"
    else:
        e["clips"] = clips
    os_ = sc.get("on_screen") or {}
    ov = []
    if os_.get("title") and sc.get("role") == "hook":
        ov.append({"type": "title", "text": os_["title"], "start": 0.4, "duration": 3.5})
    if os_.get("badge"):
        ov.append({"type": "badge", "text": os_["badge"]})
    if os_.get("lower_third"):
        lt = {"type": "lower_third", "text": os_["lower_third"], "start": 0.8}
        if os_.get("lower_third_sub"):
            lt["subtitle"] = os_["lower_third_sub"]
        ov.append(lt)
    if os_.get("callout"):
        ov.append({"type": "callout", "text": os_["callout"], "start": 6})
    if os_.get("cta"):
        ov.append({"type": "cta", "text": os_["cta"], "start": 0.5, "duration": "scene"})
    if ov and e.get("type") != "card":
        e["overlays"] = ov
    return e


def build(prod: Production, log, placeholders=False):
    prod.require("script", why="Write and check the script first.")
    s = load_script(prod)
    wpm = float(s.get("words_per_minute") or 155)
    music = prod.meta.get("music") or {}
    missing = []
    scenes = [_scene_entry(prod, sc, wpm, missing, placeholders) for sc in s.get("scenes") or []]
    audio = {}
    if music.get("file"):
        audio = {"music": music["file"], "music_license": music.get("license", "")}
    src = prod.p("script", "script.yaml")
    src_md5 = hashlib.md5(src.read_bytes()).hexdigest()
    tl = {"project": {"title": s.get("title") or prod.title, "output": prod.slug, "format": "long",
                      "source_script": rel(src), "source_script_md5": src_md5,
                      "source_script_status": str(s.get("status") or "")[:120]},
          "audio": audio, "subtitles": {"mode": "auto"}, "intro": {"position": "after_first_scene"},
          "scenes": scenes}
    path = prod.p("edit", "timeline.yaml")
    save_yaml(path, tl, f"# GENERATED by studio.py build-timeline from script/script.yaml - {prod.slug}\n"
                        "# You can edit it, but it is regenerated when you run build-timeline / render again.")
    # ---- shorts (explicit scenes so vertical '-v' clips are used when available)
    by_id = {sc["id"]: sc for sc in s.get("scenes") or []}
    research = load_research(prod)
    pnames = {p["id"]: (p.get("short_name") or fval(p["name"])) for p in research.get("products", [])}
    shorts = []
    smissing = []
    n_products = sum(1 for sc in s.get("scenes") or [] if sc.get("role") == "product")
    dedicated = {sh["id"] for sh in dedicated_shorts(s)}
    for k, sh in enumerate(s.get("shorts") or [], 1):
        item = {"output": f"{prod.slug}-short-{k}", "title": sh.get("title") or pnames.get(sh.get("product"), ""),
                "hook": sh.get("hook")}
        if sh.get("id") in dedicated:
            # standalone Short: its own narration, voice file (voice/<short-id>.mp3), vertical shots and ending.
            # A graphic shot of kind 'cta' becomes the closing call-to-action text instead of a full card.
            cta = next((x.get("text") for x in sh.get("shots") or []
                        if x.get("type") == "graphic" and x.get("graphic") == "cta"), "")
            body = [x for x in sh.get("shots") or [] if not (x.get("type") == "graphic" and x.get("graphic") == "cta")]
            src_scene = next((by_id[u] for u in sh.get("use_scenes") or [] if u in by_id), {})
            lt = (src_scene.get("on_screen") or {}).get("lower_third")
            pseudo = {"id": sh["id"], "narration": sh["narration"], "shots": body,
                      "on_screen": {"lower_third": lt} if lt else {}}
            item.update({"narration": " ".join(sh["narration"].split()), "cta": {"text": cta or ""},
                         "scenes": [_scene_entry(prod, pseudo, wpm, smissing, placeholders, vertical=True)]})
        else:
            # legacy: re-use long-video scenes (their voice-over) reframed to 9:16
            item.update({"cta": {"text": f"Full top {n_products} on the channel"},
                         "scenes": [_scene_entry(prod, by_id[u], wpm, smissing, placeholders, vertical=True)
                                    for u in sh.get("use_scenes") or [] if u in by_id]})
        shorts.append(item)
    sdoc = {"defaults": {"audio": audio}, "shorts": shorts}
    spath = prod.p("edit", "shorts.yaml")
    save_yaml(spath, sdoc, f"# GENERATED by studio.py build-timeline - Shorts for {prod.slug}")
    log.info(f"Timeline: {rel(path)} ({len(scenes)} scenes)")
    log.info(f"Shorts:   {rel(spath)} ({len(shorts)} Shorts, {len(dedicated)} with their own narration)")
    if not music.get("file"):
        log.info("   note: no background music set (production.yaml -> music: {file:, license:})")
    if missing:
        log.info(f"   {len(missing)} item(s) not imported yet:")
        for m in missing:
            log.info(f"     - {m}")
    return path, spath, missing
