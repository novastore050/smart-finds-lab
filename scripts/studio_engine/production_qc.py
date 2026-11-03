"""Final production QC: one report that combines every automated check, plus a human review checklist.

Automated = measured by software (files, durations, codecs, loudness, data/claim rules).
Human review = things only a person can judge (does it look right, is it accurate, is it good).
The report never ticks a human item; the owner records approval with  studio.py review-done.
"""
from __future__ import annotations

import json
import re
import subprocess

from sfl_engine.qc import ICON
from sfl_engine.util import ROOT, find_tool, probe, rel

from .common import Production, fval, fverified, now
from .prompts import shot_file
from .research import load_research, products_by_rank, validate, verification_summary
from .script import check as script_check
from .script import load_script
from .voice import scene_audio

SECRET_PATTERNS = [r"sk_[A-Za-z0-9]{20,}", r"xi-api-key\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}", r"AKIA[0-9A-Z]{16}",
                   r"AIza[0-9A-Za-z_\-]{35}", r"ghp_[A-Za-z0-9]{36}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"]


def scan_secrets(paths) -> list:
    hits = []
    for base in paths:
        for f in base.rglob("*"):
            if f.is_file() and f.suffix.lower() in {".py", ".yaml", ".yml", ".json", ".md", ".txt", ".csv", ".env",
                                                    ".srt", ".sh", ".toml", ".ini", ".cfg"} and f.stat().st_size < 2e6:
                text = f.read_text(encoding="utf-8", errors="ignore")
                for pat in SECRET_PATTERNS:
                    if re.search(pat, text):
                        hits.append(f"{rel(f)} matches {pat[:18]}…")
    return hits


def decode_ok(path) -> tuple[bool, str]:
    """Export integrity: decode every frame; any decoder error means a damaged file."""
    p = subprocess.run([find_tool("ffmpeg"), "-v", "error", "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    err = p.stderr.strip()
    return (p.returncode == 0 and not err), err[:300]


def run(prod: Production, log, decode=True):
    items = []  # (level, area, message)

    def add(level, area, msg):
        items.append((level, area, msg))

    # ---- research
    data = load_research(prod)
    for lvl, m in validate(data, int(prod.meta.get("products_wanted", 10))):
        add("error" if lvl == "error" else "warning", "Research", m)
    if prod.done("products_approved"):
        add("ok", "Research", f"products approved by owner ({prod.meta['stages']['products_approved']['at']})")
    else:
        add("error", "Research", "products not approved by the owner yet")
    for p in products_by_rank(data):
        v = verification_summary(p)
        bad = [k for k in ("asin", "amazon_url", "price_amazon", "rating_amazon") if v[k] != "verified"]
        if bad:
            add("warning", "Verification", f"{fval(p['name'])}: not verified on Amazon: {', '.join(bad)}")
    # ---- script
    script = None
    if prod.p("script", "script.yaml").exists():
        script = load_script(prod)
        issues, st = script_check(prod, script)
        for lvl, w, m in issues:
            add(lvl, "Script", f"{w}: {m}")
        if not any(l == "error" for l, _, _ in issues):
            add("ok", "Script", f"{st['scenes']} scenes, ~{st['est_seconds'] / 60:.1f} min narration, "
                                f"honesty/claims/originality checks passed ({st['references_checked']} reference "
                                "transcripts compared)")
    else:
        add("error", "Script", "no script yet")
    # ---- assets
    if script:
        sc_ids = [sc["id"] for sc in script["scenes"]]
        no_voice = [s for s in sc_ids if not scene_audio(prod, s)]
        add("error" if no_voice else "ok", "Voice-over",
            f"missing voice for: {', '.join(no_voice)}" if no_voice else f"voice for all {len(sc_ids)} scenes")
        no_srt = [s for s in sc_ids if scene_audio(prod, s) and not prod.p("voice", f"{s}.srt").exists()]
        if no_srt:
            add("warning", "Subtitles", f"no word-level timing for {', '.join(no_srt)} - subtitles use estimated "
                                        "timing (import ElevenLabs word timings or install Whisper)")
        elif not no_voice:
            add("ok", "Subtitles", "word-level subtitle timing for every scene")
        missing = []
        for sc in script["scenes"]:
            for sh in sc.get("shots") or []:
                if not shot_file(prod, sh):
                    missing.append(sh["id"])
        add("error" if missing else "ok", "Clips & photos",
            f"{len(missing)} shot(s) not imported: {', '.join(missing[:15])}{'…' if len(missing) > 15 else ''}"
            if missing else "every shot has a file")
    # ---- renders
    longv = ROOT / "output" / "long-videos" / f"{prod.slug}.mp4"
    outputs = [("Long video", longv, (1920, 1080), None)]
    for k in range(1, 4):
        outputs.append((f"Short {k}", ROOT / "output" / "shorts" / f"{prod.slug}-short-{k}.mp4", (1080, 1920), (15, 61)))
    for label, f, dims, rng in outputs:
        if not f.exists():
            add("error", label, f"not rendered yet ({rel(f)})")
            continue
        info = probe(f)
        ok_dims = (info["width"], info["height"]) == dims
        add("ok" if ok_dims else "error", label, f"{info['width']}x{info['height']}, {info['vcodec']}/{info['acodec']}, "
                                                 f"{info['duration']:.1f}s")
        if rng and not rng[0] <= info["duration"] <= rng[1]:
            add("warning", label, f"length {info['duration']:.1f}s outside 20-60 s target")
        qj = f.with_suffix(".qc.json")
        if qj.exists():
            q = json.loads(qj.read_text())
            lvl = {"PASS": "ok", "PASS WITH WARNINGS": "warning"}.get(q["status"], "error")
            add(lvl, label, f"render QC: {q['status']} (see {rel(f.with_suffix('.qc.md'))})")
            for c in q["checks"]:
                if c["area"] in ("Audio sync", "Loudness", "Black frames", "Silence") and c["level"] != "ok":
                    add("warning", label, f"{c['area']}: {c['message']}")
        if decode:
            good, err = decode_ok(f)
            add("ok" if good else "error", label, "export integrity: every frame decodes without errors" if good
                else f"decode errors: {err}")
    # ---- thumbnails
    thumbs = sorted(prod.p("thumbnails").glob("*.jpg"))
    if not thumbs:
        add("error", "Thumbnail", "no thumbnail generated")
    for t in thumbs:
        i = probe(t)
        size = t.stat().st_size / 1e6
        good = (i["width"], i["height"]) == (1280, 720) and size < 2
        add("ok" if good else "error", "Thumbnail", f"{t.name}: {i['width']}x{i['height']}, {size:.2f} MB")
    # ---- SEO
    sj = prod.p("seo", "youtube.json")
    if not sj.exists():
        add("error", "SEO", "no SEO pack")
    else:
        seo = json.loads(sj.read_text())
        d = seo["description"]
        add("ok" if len(d) <= 5000 else "error", "SEO", f"description {len(d)} characters (max 5000)")
        add("ok" if "Amazon Associate" in d else "error", "SEO", "affiliate disclosure in description"
            if "Amazon Associate" in d else "affiliate disclosure MISSING")
        bad_t = [t for t in seo["titles"] if len(t) > 100]
        add("error" if bad_t else "ok", "SEO", f"{len(seo['titles'])} title options, all ≤ 100 characters"
            if not bad_t else f"titles too long: {bad_t}")
        ch = seo["chapters"]
        ch_ok = len(ch) >= 3 and ch[0][0] == 0
        add("ok" if ch_ok else "error", "SEO", f"{len(ch)} chapters starting at 0:00" if ch_ok else "chapters invalid")
        if seo.get("chapters_dropped"):
            add("warning", "SEO", f"chapters left out (under 10 s): {', '.join(seo['chapters_dropped'])}")
        if seo.get("chapters_estimated"):
            add("warning", "SEO", "chapter times are estimated - regenerate SEO after voice import")
        if "[Amazon link to add]" in d or "[link to add]" in json.dumps(seo["shorts"]):
            add("warning", "SEO", "some Amazon links are still missing")
        if seo.get("unverified_links"):
            add("warning", "SEO", f"unverified Amazon links: {', '.join(seo['unverified_links'])}")
    # ---- secrets
    hits = scan_secrets([prod.dir, ROOT / "config", ROOT / "scripts"])
    add("error" if hits else "ok", "Secrets", "; ".join(hits) if hits else "no API keys or tokens found in project files")

    # ---- report
    order = {"error": 0, "warning": 1, "ok": 2}
    n_err = sum(1 for i in items if i[0] == "error")
    n_warn = sum(1 for i in items if i[0] == "warning")
    status = "FAIL" if n_err else ("PASS WITH WARNINGS" if n_warn else "PASS")
    ico = {"error": ICON["error"], "warning": ICON["warning"], "ok": ICON["ok"]}
    L = [f"# Final production QC — {prod.title}", "", f"Generated: {now()}  ", f"**Automated status: {status}** "
         f"({n_err} errors, {n_warn} warnings)  ",
         f"**Human review: {'✅ approved ' + prod.meta['stages']['human_review']['at'] if prod.done('human_review') else '⏳ NOT DONE'}**",
         "", "## Part A — Automated checks (measured by software)", "", "| | Area | Result |", "|---|---|---|"]
    for lvl, area, msg in sorted(items, key=lambda i: order[i[0]]):
        L.append(f"| {ico[lvl]} | {area} | {msg.replace('|', '/')} |")
    L += ["", "## Part B — Human review (only a person can check these — nothing below is automated)", "",
          "- [ ] Watched the whole long video at normal speed, with sound",
          "- [ ] Every product name, badge number and on-screen text is correct",
          "- [ ] AI b-roll does not misrepresent any product (shape, size, features)",
          "- [ ] Nothing in the narration claims hands-on testing that did not happen",
          "- [ ] Voice sounds natural; no mispronounced brand names",
          "- [ ] Subtitles match what is said",
          "- [ ] Each Short: the product is visible, captions readable, nothing under YouTube's buttons",
          "- [ ] Thumbnail is readable on a phone and not misleading",
          "- [ ] Amazon links open the right products; prices were checked recently",
          "- [ ] Music licence noted; all footage/photos are yours or licensed",
          "- [ ] YouTube settings: affiliate disclosure, altered-content setting (if realistic AI), not made for kids",
          "", f"When everything above is checked, record it:  `python scripts/studio.py review-done {prod.slug}`",
          "", "*Automated checks cannot judge quality, accuracy or taste. A PASS here does not mean the video is "
          "ready to publish until Part B is done.*"]
    out = prod.p("reports", "production-qc.md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    prod.mark("qc", status)
    log.info(f"Production QC: {status} ({n_err} errors, {n_warn} warnings) -> {rel(out)}")
    return status, items
