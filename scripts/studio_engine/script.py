"""Script: draft an original scene-by-scene script from approved research, and check it.

script/script.yaml is the single source for narration, on-screen text and shots.
The draft is built only from researched facts (no invented numbers). Prices are never
spoken; star ratings / rating counts are only used when VERIFIED on Amazon.
"""
from __future__ import annotations

import re
from pathlib import Path

from sfl_engine.qc import CLAIM_PATTERNS
from sfl_engine.util import ROOT, SFLError, rel

from .common import Production, fval, fverified, load_yaml, save_yaml, today
from .research import load_research, products_by_rank


def studio_cfg() -> dict:
    return load_yaml(ROOT / "config" / "studio.yaml")


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9'$%.]+", text or ""))


def est_seconds(text: str, wpm: float) -> float:
    return round(words(text) / wpm * 60, 1)


def _sentence(t: str) -> str:
    t = str(t or "").strip()
    if t and t[-1] not in ".!?":
        t += "."
    return t[:1].upper() + t[1:] if t else t


NUM_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
             10: "ten", 11: "eleven", 12: "twelve"}


# ---------------------------------------------------------------------------- draft
def draft(prod: Production, log, force=False):
    prod.require("products_approved", force, "Approve the products first: python scripts/studio.py approve-products "
                 + prod.slug)
    cfg = studio_cfg()
    data = load_research(prod)
    approved = set(prod.meta.get("approved_products") or [])
    prods = [p for p in products_by_rank(data) if not approved or p["id"] in approved]
    if not prods:
        raise SFLError("No shortlisted products to write about")
    n = len(prods)
    out = prod.p("script", "script.yaml")
    if out.exists() and not force:
        raise SFLError(f"{rel(out)} already exists (you may have edited it). Use --force to overwrite.")
    vtype = prod.meta.get("video_type", "research_based")
    scenes = []
    topic = prod.meta.get("topic_noun") or "gadgets"
    hook = (f"Most {topic} sound great online and then barely get used. These {NUM_WORDS.get(n, n)} are different. "
            "We went through customer reviews, specs and expert roundups to find the ones people actually keep using. "
            "We'll count down to number one, and it fixes a job you probably do every single day.")
    scenes.append({"id": "s01", "role": "hook", "narration": hook,
                   "on_screen": {"title": prod.title},
                   "shots": _hook_shots(prods, cfg)})
    for i, p in enumerate(reversed(prods)):  # countdown: highest rank number first
        sid = f"s{i + 2:02d}"
        rank = p["rank"]
        name = fval(p["name"])
        short_name = p.get("short_name") or name
        parts = [f"Number {NUM_WORDS.get(rank, rank)}: the {short_name}."]
        if p.get("angle"):
            parts.append(_sentence(p["angle"]))
        feats = [f["text"] for f in (p.get("features") or [])][:2]
        parts += [_sentence(f) for f in feats]
        pros = [x["text"] for x in (p.get("pros") or [])][:2]
        if pros:
            parts.append("What buyers like most: " + " ".join(_sentence(x) for x in pros))
        claims = []
        rat, cnt = p.get("rating_amazon") or {}, p.get("review_count_amazon") or {}
        if fverified(rat) and fverified(cnt) and fval(rat) and fval(cnt):
            c = int(fval(cnt))
            approx = f"{(c // 1000) * 1000:,}" if c >= 2000 else f"{(c // 100) * 100:,}"
            line = f"On Amazon it's rated {fval(rat)} stars from over {approx} ratings, as of {rat.get('as_of')}."
            parts.append(line)
            claims.append({"text": line, "fields": [f"{p['id']}.rating_amazon", f"{p['id']}.review_count_amazon"]})
        cons = [x["text"] for x in (p.get("cons") or [])][:1]
        if cons:
            parts.append("The downside: " + _sentence(cons[0]))
        if p.get("best_for"):
            parts.append(_sentence(f"It's best for {p['best_for']}"))
        on_screen = {"badge": f"#{rank}", "lower_third": short_name[:int(cfg['script']['lower_third_max_chars'])],
                     "lower_third_sub": f"Best for: {p['best_for']}"[:44] if p.get("best_for") else ""}
        if p.get("callout"):
            on_screen["callout"] = p["callout"]
        scenes.append({"id": sid, "role": "product", "product": p["id"], "rank": rank, "basis": vtype,
                       "narration": " ".join(parts), "on_screen": on_screen, "claims": claims,
                       "shots": _product_shots(sid, p, cfg)})
    wrap = ("Prices on these change all the time, so check the links in the description for today's price. "
            "Which one would you grab first? Tell us in the comments, and subscribe for more smart finds.")
    scenes.append({"id": f"s{n + 2:02d}", "role": "wrapup", "narration": wrap,
                   "on_screen": {"cta": "Links in the description"},
                   "shots": [{"id": f"s{n + 2:02d}-a", "type": "ai_broll", "aspect": "16:9",
                              "prompt": "slow wide shot of a tidy, well-organized kitchen counter with a few simple tools "
                                        "laid out neatly, a hand placing a cutting board down"}]})
    for sc in scenes:
        for sh in sc.get("shots") or []:
            if sh.get("file"):
                sh["file"] = sh["file"].replace("{slug}", prod.slug)
    top3 = prods[:3]
    shorts = []
    for k, p in enumerate(top3, 1):
        sid = next(s["id"] for s in scenes if s.get("product") == p["id"])
        shorts.append({"id": f"short{k}", "product": p["id"], "use_scenes": [sid],
                       "hook": p.get("shorts_hook") or f"The kitchen tool buyers keep recommending",
                       "title": f"{p.get('short_name') or fval(p['name'])} — worth it?"})
    doc = {"title": prod.title, "status": "draft", "drafted": today(), "video_type": vtype,
           "audience": "US English", "words_per_minute": cfg["script"]["words_per_minute"],
           "notes": "Edit narration freely. Keep it original, keep claims sourced. Re-run check-script after edits.",
           "scenes": scenes, "shorts": shorts}
    save_yaml(out, doc, "# SCRIPT - one entry per scene. Narration is what the voice says.\n"
                        "# on_screen = graphics. shots = clips to create (see prompts/).")
    log.info(f"Draft script written: {rel(out)}  ({len(scenes)} scenes, {len(shorts)} Shorts)")
    return out


def _vis(p, key, default):
    return str(p.get(key) or default).strip().rstrip(".")


def _hook_shots(prods, cfg):
    shots = []
    for k, p in enumerate(prods[:3]):
        shots.append({"id": f"s01-{'abc'[k]}", "type": "ai_broll", "aspect": "16:9", "product": p["id"],
                      "prompt": f"quick close-up of hands using {_vis(p, 'visual_description', 'a kitchen tool')}, "
                                f"{_vis(p, 'broll_use', 'in a home kitchen')}"})
    return shots


def _product_shots(sid, p, cfg):
    desc = _vis(p, "visual_description", "a simple kitchen tool")
    return [
        {"id": f"{sid}-a", "type": "ai_broll", "aspect": "16:9", "product": p["id"],
         "prompt": _vis(p, "broll_problem", f"a person struggling with a messy kitchen task")},
        {"id": f"{sid}-b", "type": "ai_broll", "aspect": "16:9", "product": p["id"],
         "prompt": f"close-up of hands using {desc}, {_vis(p, 'broll_use', 'on a wooden cutting board')}"},
        {"id": f"{sid}-photo", "type": "product_photo", "product": p["id"],
         "file": f"assets/images/{{slug}}/{p['id']}.jpg",
         "prompt": "Real product photo (your own photo, or a manufacturer image you are allowed to use). "
                   "Identifies the actual product - AI clips above are generic b-roll."},
    ]


# ---------------------------------------------------------------------------- checks
PRICE_RE = re.compile(r"\$\s?\d|\b\d+(?:\.\d+)?\s?(?:dollars|bucks)\b", re.I)
RATING_RE = re.compile(r"\b\d(?:\.\d)?\s*(?:stars?|out of (?:5|five))\b", re.I)
COUNT_RE = re.compile(r"\b\d[\d,]*\s*(?:\+\s*)?(?:ratings|reviews|reviewers|buyers|customers)\b", re.I)


def load_script(prod: Production) -> dict:
    return load_yaml(prod.p("script", "script.yaml"))


def reference_texts():
    """Owner-provided transcripts of reference videos (kept out of git)."""
    out = []
    for f in (ROOT / "references").glob("*/transcripts/*.txt"):
        out.append((rel(f), f.read_text(encoding="utf-8", errors="replace")))
    return out


def _ngrams(text, n):
    w = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def check(prod: Production, script: dict | None = None):
    cfg = studio_cfg()
    s = script or load_script(prod)
    data = load_research(prod)
    by_id = {p["id"]: p for p in data.get("products", [])}
    wpm = float(s.get("words_per_minute") or cfg["script"]["words_per_minute"])
    vtype = s.get("video_type", "research_based")
    issues = []  # (level, where, message)
    total = 0.0
    refs = reference_texts()
    n = int(cfg["script"].get("originality_ngram", 7))
    ref_grams = [(name, _ngrams(t, n)) for name, t in refs]
    seen_ids = set()
    approved = set(prod.meta.get("approved_products") or [])
    for sc in s.get("scenes") or []:
        sid = sc.get("id", "?")
        if sid in seen_ids:
            issues.append(("error", sid, "duplicate scene id"))
        seen_ids.add(sid)
        text = sc.get("narration") or ""
        sec = est_seconds(text, wpm)
        total += sec
        if not text.strip():
            issues.append(("error", sid, "no narration"))
        if re.search(r"\[[^\]]+\]", text):
            issues.append(("warning", sid, "narration still contains [placeholder] text"))
        role = sc.get("role")
        if role == "hook" and sec > float(cfg["script"]["hook_max_seconds"]):
            issues.append(("warning", sid, f"hook is ~{sec:.0f}s - aim for under {cfg['script']['hook_max_seconds']}s"))
        if role == "product" and sec > float(cfg["script"]["product_max_seconds"]):
            issues.append(("warning", sid, f"~{sec:.0f}s is long for one product"))
        # honesty: testing claims
        basis = sc.get("basis", vtype)
        if basis == "hands_on":
            ho = sc.get("hands_on") or {}
            if not (ho.get("tested_by") and ho.get("date")):
                issues.append(("error", sid, "basis is hands_on but no 'hands_on: {tested_by, date, notes}' record"))
        else:
            for pat in CLAIM_PATTERNS:
                m = re.search(pat, text, re.I)
                if m:
                    issues.append(("error", sid, f"says \"{m.group(0)}\" but this is a research-based video"))
        # numbers must be verified
        claimed = " ".join(c.get("text", "") for c in sc.get("claims") or [])
        for c in sc.get("claims") or []:
            for f in c.get("fields") or []:
                pid, _, field = f.partition(".")
                if not fverified((by_id.get(pid) or {}).get(field)):
                    issues.append(("error", sid, f"claim uses {f}, which is NOT verified on Amazon"))
        if PRICE_RE.search(text):
            issues.append(("error", sid, "narration states a price - prices go out of date; say 'check today's price' "
                                         "instead (and keep exact prices out of the video)"))
        for rx, what in ((RATING_RE, "star rating"), (COUNT_RE, "rating/review count")):
            for m in rx.finditer(text):
                if m.group(0) not in claimed:
                    issues.append(("error", sid, f"mentions a {what} (\"{m.group(0)}\") that is not a registered, "
                                                 "verified claim"))
        # product link
        if role == "product":
            pid = sc.get("product")
            if pid not in by_id:
                issues.append(("error", sid, f"unknown product '{pid}'"))
            elif approved and pid not in approved:
                issues.append(("error", sid, f"product '{pid}' was not approved"))
            if not any(sh.get("type") == "product_photo" for sh in sc.get("shots") or []):
                issues.append(("warning", sid, "no real product photo shot - AI b-roll alone may misrepresent the product"))
            lt = (sc.get("on_screen") or {}).get("lower_third", "")
            if len(lt) > int(cfg["script"]["lower_third_max_chars"]):
                issues.append(("warning", sid, f"lower third is long ({len(lt)} chars)"))
        if not sc.get("shots"):
            issues.append(("warning", sid, "no shots listed"))
        # originality vs reference transcripts
        mine = _ngrams(text, n)
        for name, grams in ref_grams:
            common = mine & grams
            if common:
                issues.append(("error", sid, f"{len(common)} phrase(s) of {n}+ words match reference {name}, e.g. "
                                             f"\"{sorted(common)[0]}\" - rewrite in your own words"))
    for sh in s.get("shorts") or []:
        for u in sh.get("use_scenes") or []:
            if u not in seen_ids:
                issues.append(("error", sh.get("id", "short"), f"uses unknown scene '{u}'"))
    if len(s.get("shorts") or []) != 3:
        issues.append(("warning", "shorts", f"{len(s.get('shorts') or [])} Shorts planned (3 wanted)"))
    stats = {"scenes": len(s.get("scenes") or []), "est_seconds": round(total, 1), "wpm": wpm,
             "references_checked": len(refs)}
    return issues, stats


def write_markdown(prod: Production):
    s = load_script(prod)
    issues, st = check(prod, s)
    wpm = st["wpm"]
    L = [f"# Script — {s.get('title')}", "", f"Status: **{s.get('status')}** · Type: **{s.get('video_type')}** · "
         f"Estimated length: **{int(st['est_seconds'] // 60)}:{int(st['est_seconds'] % 60):02d}** "
         f"(+ intro/outro cards) at {wpm:.0f} words/min", ""]
    if issues:
        L += ["## Script checks", ""] + [f"- {'❌' if l == 'error' else '⚠️'} **{w}**: {m}" for l, w, m in issues] + [""]
    else:
        L += ["✅ All script checks passed.", ""]
    for sc in s.get("scenes") or []:
        sec = est_seconds(sc.get("narration", ""), wpm)
        L += [f"## {sc['id']} · {sc.get('role')}{(' · #' + str(sc['rank'])) if sc.get('rank') else ''} · ~{sec:.0f}s", "",
              f"> {sc.get('narration', '')}", ""]
        os_ = sc.get("on_screen") or {}
        if os_:
            L.append("**On screen:** " + " · ".join(f"{k}: *{v}*" for k, v in os_.items() if v))
        for sh in sc.get("shots") or []:
            L.append(f"- shot `{sh['id']}` ({sh.get('type')}): {sh.get('prompt', '')}")
        if sc.get("needs_verification"):
            L.append("")
            L += [f"- ⚠️ **Needs verification:** {v}" for v in sc["needs_verification"]]
        L.append("")
    if s.get("shorts"):
        L += ["## Shorts", ""] + [f"- **{x['id']}**: hook \"{x.get('hook')}\" — scenes {x.get('use_scenes')}"
                                  for x in s["shorts"]]
    prod.p("script", "script.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return issues, st
