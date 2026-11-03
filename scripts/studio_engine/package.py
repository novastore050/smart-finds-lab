"""Production package: one folder (production/) with everything needed to make the video by hand or with tools.

Writes: production/README.md (index), shorts-scripts.md, voiceover-sections.md, thumbnail-concepts.md,
production-checklist.md. The visual plan (visual-plan.md) comes from `studio.py plan`.
Nothing here generates paid media.
"""
from __future__ import annotations

import json

from sfl_engine.util import rel

from .common import Production, fval
from .research import load_research, products_by_rank, verification_summary
from .script import est_seconds, load_script, studio_cfg
from .voice import voice_cfg


def write(prod: Production, log):
    prod.require("script", why="Write and check the script first.")
    out = prod.dir / "production"
    out.mkdir(parents=True, exist_ok=True)
    s = load_script(prod)
    wpm = float(s.get("words_per_minute") or 155)
    data = load_research(prod)
    byid = {p["id"]: p for p in data.get("products", [])}
    scenes = {sc["id"]: sc for sc in s.get("scenes") or []}
    vc = voice_cfg()
    cfg = studio_cfg()

    # ---- Shorts scripts
    L = [f"# Shorts scripts — {prod.title}", "",
         "Each Short re-uses one product scene from the long video (same voice-over and footage, reframed to 9:16 "
         "by the editor; vertical `-v` clips are used when available). Target 20–60 s.", ""]
    for k, sh in enumerate(s.get("shorts") or [], 1):
        body = [scenes[u] for u in sh.get("use_scenes") or [] if u in scenes]
        sec = sum(est_seconds(x.get("narration", ""), wpm) for x in body) + 0.6
        p = byid.get(sh.get("product"), {})
        L += [f"## Short {k}: {sh.get('title')}", "",
              f"- Product: **{fval(p.get('name'))}** (ASIN {fval(p.get('asin'))}, unverified)",
              f"- Estimated length: **~{sec:.0f} s** {'✅ within 20–60 s' if 20 <= sec <= 60 else '⚠️ outside 20–60 s'}",
              f"- Hook text on screen (0–3 s): **{sh.get('hook')}**",
              "- Captions: big 1–3 word captions with one highlighted word (automatic)",
              f"- End card (last 2.5 s): **Full top {sum(1 for x in s['scenes'] if x.get('role') == 'product')} on the channel**",
              f"- YouTube title: {sh.get('title')} #Shorts", "", "**Voice-over (from the long video):**", ""]
        L += [f"> {x.get('narration', '')}" for x in body] + [""]
        first = (body[0].get("narration", "") if body else "").split(":")[0]
        if first.lower().startswith(("number", "and number")):
            L += [f"*Edit tip:* the voice starts with \"{first}:\" — once the audio exists, trim it for the Short "
                  "by setting `voice_start` on that scene in `edit/shorts.yaml`.", ""]
        nv = [v for x in body for v in x.get("needs_verification") or []]
        if nv:
            L += ["**Verify first:** " + "; ".join(nv), ""]
    (out / "shorts-scripts.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---- Voice-over sections
    jobs = json.loads(prod.p("voice", "voice-jobs.json").read_text())
    L = [f"# Voice-over sections — {prod.title}", "",
         f"Voice: **{vc['voice']['name']}** (`{vc['voice']['voice_id']}`) · model `{vc['model_id']}` · "
         f"output `{vc.get('output_format')}`", "",
         "Settings (keep identical for every video): " + ", ".join(f"`{k}: {v}`" for k, v in vc["voice_settings"].items()),
         "", f"Total: **{jobs['total_characters']:,} characters** in {len(jobs['jobs'])} sections — roughly the same "
             "number of ElevenLabs credits on standard models per take (estimate; check with an `estimate_only` call). "
             "**Nothing has been generated.**", "",
         "## Pronunciation notes", "", "Applied automatically to the voice text only (subtitles keep the real spelling):", ""]
    L += [f"- **{w}** → say *{say}*" for w, say in (vc.get("pronunciations") or {}).items()]
    L += ["- **Zulay** pronunciation is a guess — confirm before generating.",
          "- Numbers are written as words in the script (\"Number ten\", \"double-A\") so the voice reads them naturally.",
          "", "## Sections", "",
          "| # | Scene | Characters | ~Seconds | Text file | Save audio as |", "|---|---|---|---|---|---|"]
    for i, j in enumerate(jobs["jobs"], 1):
        L.append(f"| {i} | {j['scene']} | {j['chars']} | {j['est_seconds']} | `voice/text/{j['scene']}.txt` | "
                 f"`{j['save_audio_as']}` |")
    L += ["", "Delivery notes: warm, confident, conversational; slight pause after \"Number …:\"; lighter tone on the "
          "downsides (honest, not negative); smile on the call to action."]
    (out / "voiceover-sections.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---- Thumbnail concepts
    th = (prod.meta.get("thumbnail") or {}).get("variants") or []
    top = products_by_rank(data)[:3]
    L = [f"# Thumbnail concepts — {prod.title}", "",
         "1280×720 · readable on a phone · one hero product · no fake faces or reactions · no prices · no claims we "
         "can't back up. Mockups (brand background only) are generated by `studio.py thumbnail` into `thumbnails/`; "
         "the final versions need your real product photos in `assets/images/<slug>/`.", ""]
    for k, v in enumerate(th):
        L += [f"## Concept {chr(65 + k)}", "", f"- Big text: **{v['text']}**", f"- Sub text: {v.get('sub', '')}",
              f"- Badge: {v.get('badge', '')}"]
        L.append(f"- Hero image: {fval(top[k % len(top)]['name'])} (real photo), cut out on the dark brand background"
                 if top else "")
        L.append("")
    L += ["## Concept C (optional)", "", "- Split image: messy problem (left, desaturated) vs clean result (right)",
          "- Big text: **These Actually Help**", "- Hero: egg cooker with steam (photo)", "",
          "Test A vs B with YouTube's thumbnail test feature after upload."]
    (out / "thumbnail-concepts.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---- Checklist
    short = products_by_rank(data)
    unver = [fval(p["short_name"] if p.get("short_name") else p["name"]) for p in short
             if verification_summary(p)["rating_amazon"] != "verified"]
    L = [f"# Production checklist — {prod.title}", "",
         "Tick in order. Commands run from the Smart-Finds-Lab folder.", "",
         "## 1. Facts (before any spending)",
         "- [x] Products approved (Version 4)",
         f"- [ ] Fill `research/amazon-verification.csv` on Amazon.com, then `python scripts/studio.py import-verification {prod.slug}`",
         f"- [ ] Resolve every \"needs verification\" note in `script/script.md` ({len(unver)} products have no verified Amazon rating)",
         "- [ ] Confirm Zulay pronunciation",
         "", "## 2. Assets",
         "- [ ] Choose the voice (listen to `productions/_voice-samples/`), set `status: chosen` in `config/voice.yaml`",
         f"- [ ] Approve ElevenLabs cost (~{jobs['total_characters']:,} characters per take), generate, then "
         f"`import-voice` + `align`",
         f"- [ ] Generate Higgsfield clips from `prompts/higgsfield-prompts.md` (needs paid credits), then "
         f"`import-clips {prod.slug} <folder>`",
         "- [ ] Add real product photos to `assets/images/<slug>/<product-id>.jpg` (yours or licensed)",
         "- [ ] Add licensed background music and set `music:` in `production.yaml`",
         "", "## 3. Edit",
         f"- [ ] `python scripts/studio.py render {prod.slug} --draft` and watch it",
         f"- [ ] `python scripts/studio.py render {prod.slug}` (long video + 3 Shorts + thumbnails + SEO + QC)",
         "", "## 4. Before upload",
         "- [ ] Part B of `reports/production-qc.md` completed, then `review-done`",
         "- [ ] Amazon Associates tag set in `config/studio.yaml` (if you have one); links checked",
         "- [ ] YouTube: title/description/tags/chapters from `seo/youtube.md`; upload `.srt`; affiliate disclosure;",
         "      altered-content setting if realistic AI scenes; not made for kids",
         "- [ ] Upload manually (nothing is published automatically)"]
    (out / "production-checklist.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---- Index
    idx = [f"# Production package — {prod.title}", "", "| What | File |", "|---|---|",
           "| Final script (readable, with verification flags) | `script/script.md` |",
           "| Script source (edit this) | `script/script.yaml` |",
           "| Scene-by-scene visual plan | `production/visual-plan.md` |",
           "| Higgsfield prompts / shot list | `prompts/higgsfield-prompts.md`, `prompts/shotlist.csv` |",
           "| Voice-over sections + settings + pronunciation | `production/voiceover-sections.md`, `voice/text/` |",
           "| Voice recommendation | `production/voice-recommendation.md` |",
           "| Shorts scripts (3) | `production/shorts-scripts.md` |",
           "| Thumbnail concepts | `production/thumbnail-concepts.md`, mockups in `thumbnails/` |",
           "| Titles, description, tags, chapters | `seo/youtube.md` |",
           "| Editor timelines | `edit/timeline.yaml`, `edit/shorts.yaml` |",
           "| Research + approved shortlist | `research/` |",
           "| Reference channel analysis + creative direction | `research/reference-channels/` |",
           "| Checklist | `production/production-checklist.md` |",
           "| Quality report | `reports/production-qc.md` |"]
    (out / "README.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    log.info(f"Package written to {rel(out)}/")
    return out
