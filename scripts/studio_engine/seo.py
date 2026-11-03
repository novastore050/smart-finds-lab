"""YouTube SEO pack: titles, description (chapters, links, disclosures), tags, Shorts metadata, pinned comment.

Chapters come from the real editing plan (scene start times). If voice-overs are not imported yet,
scene lengths are estimates and the pack says so. Nothing is uploaded or published.
"""
from __future__ import annotations

import datetime as dt
import json

from sfl_engine.builder import add_bookends
from sfl_engine.config import load_timeline
from sfl_engine.plan import make_plan
from sfl_engine.util import rel

from .common import Production, fval, fverified
from .research import load_research
from .script import load_script, studio_cfg
from .voice import scene_audio


def _ts(t):
    t = int(t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def link(url, tag):
    if not url:
        return None
    if tag:
        return url + ("&" if "?" in url else "?") + f"tag={tag}"
    return url


def chapters(prod: Production, script: dict, names: dict):
    proj = load_timeline(prod.p("edit", "timeline.yaml"))
    add_bookends(proj)
    plan = make_plan(proj, None, allow_missing=True)
    roles = {sc["id"]: sc for sc in script.get("scenes") or []}
    out = []
    for ps in plan.scenes:
        sid = ps.scene.id
        t = (ps.start_f + ps.trans_f) / plan.fps
        sc = roles.get(sid)
        if not sc:
            continue  # intro/outro cards belong to the previous chapter
        if sc.get("role") not in ("hook", "product", "wrapup"):
            continue  # setup/bridge scenes belong to the previous chapter
        if sc.get("role") == "hook":
            label = "Intro"
            t = 0
        elif sc.get("role") == "product":
            label = f"#{sc.get('rank')} {names.get(sc.get('product'), '')}".strip()
        else:
            label = "Final thoughts"
        out.append([t, label])
    # YouTube: first chapter at 0:00, at least 3 chapters, each at least 10 s
    clean, dropped = [], []
    for t, label in out:
        if clean and t - clean[-1][0] < 10:
            dropped.append(label)  # YouTube needs >= 10 s per chapter
            continue
        clean.append([t, label])
    estimated = any(not scene_audio(prod, sc["id"]) for sc in script.get("scenes") or [])
    return clean, plan.total, estimated, dropped


def build(prod: Production, log):
    cfg = studio_cfg()
    s = load_script(prod)
    data = load_research(prod)
    byid = {p["id"]: p for p in data.get("products", [])}
    names = {pid: (p.get("short_name") or fval(p["name"])) for pid, p in byid.items()}
    tag = (cfg["channel"].get("amazon_tag") or "").strip()
    chaps, total, estimated, dropped = chapters(prod, s, names)
    title = s.get("title") or prod.title
    year = dt.date.today().year
    custom = prod.meta.get("seo") or {}
    titles = custom.get("titles") or [title, f"{title} ({year})", f"{title} | Researched & Compared"]
    titles = [t for t in titles if len(t) <= 100]
    prods = [sc for sc in s.get("scenes") or [] if sc.get("role") == "product"]
    hook = custom.get("description_intro") or (" ".join(str(s["scenes"][0].get("narration", "")).split()[:30]) + "…")
    D = [hook, "", "🛒 PRODUCTS IN THIS VIDEO (prices change — check the link for today's price):"]
    unverified_links = []
    for sc in prods:
        p = byid.get(sc.get("product"), {})
        url = fval(p.get("amazon_url"))
        if url and not fverified(p.get("amazon_url")):
            unverified_links.append(names.get(p.get("id")))
        D.append(f"#{sc.get('rank')} {fval(p.get('name'))}: {link(url, tag) or '[Amazon link to add]'}")
    D += ["", "⏱️ CHAPTERS"] + [f"{_ts(t)} {label}" for t, label in chaps]
    D += ["", "ℹ️ " + cfg["disclosure"]["affiliate"], "ℹ️ " + cfg["disclosure"]["research_based"], "",
          f"🔔 Subscribe to {cfg['channel']['name']} — {cfg['channel']['tagline']}", "",
          " ".join(cfg["seo"]["hashtags"])]
    description = "\n".join(D)
    tags = list(dict.fromkeys(custom.get("tags", []) + cfg["seo"]["default_tags"]
                              + [str(names.get(sc.get("product"), "")).lower() for sc in prods]))
    while len(",".join(tags)) > 480:
        tags.pop()
    shorts = []
    for sh in s.get("shorts") or []:
        p = byid.get(sh.get("product"), {})
        url = link(fval(p.get("amazon_url")), tag)
        st = f"{sh.get('hook') or names.get(p.get('id'))} #Shorts"
        shorts.append({"id": sh["id"], "title": st[:100],
                       "description": "\n".join([f"{fval(p.get('name'))} — part of our {title}.",
                                                 f"Amazon: {url or '[link to add]'}", "",
                                                 cfg["disclosure"]["affiliate"],
                                                 " ".join(cfg["seo"]["hashtags"] + ["#Shorts"])])})
    pinned = ("Which of these would you actually use the most? 👇 Links to every product are in the description "
              "(prices change often, so check today's price).")
    pack = {"generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "titles": titles, "description": description,
            "tags": tags, "chapters": chaps, "chapters_estimated": estimated, "chapters_dropped": dropped, "video_length_seconds": round(total, 1),
            "shorts": shorts, "pinned_comment": pinned, "unverified_links": unverified_links,
            "made_for_kids": False, "paid_promotion": "Only tick if a brand paid you or sent free products.",
            "altered_content": "Tick if realistic AI-generated scenes are used."}
    prod.p("seo", "youtube.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    M = [f"# YouTube SEO pack — {title}", "", "Nothing has been uploaded. Copy these into YouTube Studio.", ""]
    if estimated:
        M += ["> ⚠️ Chapter times are **estimates** (some voice-overs are missing). Regenerate after importing voice.", ""]
    if dropped:
        M += [f"> ⚠️ Chapters left out (shorter than YouTube's 10-second minimum): {', '.join(dropped)}.", ""]
    if unverified_links:
        M += [f"> ⚠️ Amazon links not yet verified: {', '.join(unverified_links)}. Check them before publishing.", ""]
    if not tag:
        M += ["> ℹ️ No Amazon Associates tag set (config/studio.yaml → channel.amazon_tag) — links have no affiliate tag.", ""]
    M += ["## Title options", ""] + [f"{i}. {t} *({len(t)} chars)*" for i, t in enumerate(titles, 1)]
    M += ["", "## Description", "", "```text", description, "```", "", "## Tags", "", ", ".join(tags), "",
          "## Shorts", ""]
    for x in shorts:
        M += [f"**{x['id']}** — {x['title']}", "", "```text", x["description"], "```", ""]
    M += ["## Pinned comment", "", pinned, "", "## Upload settings", "", "- Made for kids: **No**",
          f"- Paid promotion: {pack['paid_promotion']}", f"- Altered or synthetic content: {pack['altered_content']}",
          "- Upload the `.srt` from output/ as English captions."]
    prod.p("seo", "youtube.md").write_text("\n".join(M) + "\n", encoding="utf-8")
    log.info(f"SEO pack: {rel(prod.p('seo', 'youtube.md'))}  ({len(chaps)} chapters"
             f"{', ESTIMATED' if estimated else ''})")
    return pack
