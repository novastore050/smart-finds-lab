"""Pipeline orchestration: status, next step, and the render chain
(timeline -> long video -> 3 Shorts -> thumbnails -> SEO -> QC), reusing the existing FFmpeg editor."""
from __future__ import annotations

from sfl_engine import tools
from sfl_engine.builder import load_shorts, render_project
from sfl_engine.config import load_timeline
from sfl_engine.util import ROOT, SFLError, rel

from . import production_qc, seo, timeline
from .common import STAGES, Production, fval
from .prompts import shot_file, shots
from .research import load_research, products_by_rank
from .script import load_script
from .voice import scene_audio

NEXT = {
    "research": "Research products and save research/products.yaml (Claude does this with the youtube-studio skill)",
    "research_report": "python scripts/studio.py research-report {slug}",
    "products_approved": "Owner: read research/shortlist.md, verify on Amazon, then: python scripts/studio.py "
                         "approve-products {slug}",
    "script": "python scripts/studio.py draft-script {slug}   (then edit + check-script)",
    "prompts": "python scripts/studio.py prompts {slug}",
    "voice": "python scripts/studio.py voice-pack {slug}  -> generate (with approval) -> import-voice",
    "clips": "Generate clips from prompts/higgsfield-prompts.md, then: python scripts/studio.py import-clips {slug} <folder>",
    "timeline": "python scripts/studio.py build-timeline {slug}",
    "render": "python scripts/studio.py render {slug}",
    "shorts": "python scripts/studio.py render {slug}",
    "thumbnail": "python scripts/studio.py render {slug}",
    "seo": "python scripts/studio.py seo {slug}",
    "qc": "python scripts/studio.py qc {slug}",
    "human_review": "Owner: work through Part B of reports/production-qc.md, then: python scripts/studio.py "
                    "review-done {slug}",
}


def refresh(prod: Production):
    """Mark asset stages done when the files are really there (never marks manual stages)."""
    if prod.p("script", "script.yaml").exists():
        s = load_script(prod)
        if all(scene_audio(prod, sc["id"]) for sc in s.get("scenes") or []):
            prod.done("voice") or prod.mark("voice", "all scene audio present")
        elif prod.done("voice"):
            prod.unmark("voice")
        try:
            allshots = shots(prod)
            if allshots and all(shot_file(prod, sh) for sh in allshots):
                prod.done("clips") or prod.mark("clips", "all shots present")
            elif prod.done("clips"):
                prod.unmark("clips")
        except SFLError:
            pass


def status(prod: Production, log):
    refresh(prod)
    log.info(f"\n=== {prod.title}  ({rel(prod.dir)}) ===")
    nxt = None
    for key, label in STAGES:
        st = (prod.meta.get("stages") or {}).get(key)
        mark = "✅" if st else "⏳"
        log.info(f"  {mark} {label}" + (f"   [{st['at']}]" if st else ""))
        if not st and not nxt:
            nxt = key
    if prod.p("research", "products.yaml").exists():
        data = load_research(prod)
        short = products_by_rank(data)
        log.info(f"\n  Shortlist: {len(short)} products")
    if nxt:
        log.info(f"\n  NEXT: {NEXT[nxt].format(slug=prod.slug)}")
    else:
        log.info("\n  All stages done. Upload manually in YouTube Studio (nothing is published automatically).")
    return nxt


def thumbnails(prod: Production, log):
    data = load_research(prod)
    short = products_by_rank(data)
    n = len(short)
    img = None
    if short:
        img = shot_file(prod, {"type": "product_photo", "product": short[0]["id"], "id": "x"})
    video = ROOT / "output" / "long-videos" / f"{prod.slug}.mp4"
    th = prod.meta.get("thumbnail") or {}
    variants = th.get("variants") or [
        {"text": prod.title, "sub": "Researched & compared", "badge": f"TOP {n}"},
        {"text": f"{n} Picks Worth Buying", "sub": "Buyers keep these", "badge": f"TOP {n}"},
    ]
    out = []
    for k, v in enumerate(variants):
        path = prod.p("thumbnails", f"{prod.slug}-{'abcdefgh'[k]}.jpg")
        kw = {"image": str(img)} if img else ({"video": str(video), "at": 2.0} if video.exists() else {})
        tools.make_thumbnail(v["text"], v.get("sub", ""), log, badge=v.get("badge"), out_path=path, **kw)
        out.append(path)
    prod.mark("thumbnail", f"{len(out)} variants")
    return out


def render(prod: Production, log, draft=False, skip_shorts=False, placeholders=False):
    prod.require("script", why="Write and check the script first.")
    tl, sh, missing = timeline.build(prod, log, placeholders=placeholders)
    prod.mark("timeline", f"{len(missing)} items missing" if missing else "complete")
    if missing and not placeholders:
        log.info("\nSome media is missing - the render check will list it. Use --placeholders for a preview "
                 "that replaces missing clips with title cards.")
    out = render_project(load_timeline(tl), log, overwrite=True, draft=draft)
    if not out:
        raise SFLError("Long video was not rendered (see the problems above).")
    if not draft:
        prod.mark("render", rel(out))
    if not skip_shorts:
        ok = 0
        for proj in load_shorts(sh):
            try:
                if render_project(proj, log, overwrite=True, draft=draft):
                    ok += 1
            except SFLError as e:
                log.info(f"Short {proj.name} failed: {e}")
        if not draft and ok == 3:
            prod.mark("shorts", "3 Shorts rendered")
    thumbnails(prod, log)
    seo.build(prod, log)
    prod.mark("seo")
    return production_qc.run(prod, log, decode=not draft)
