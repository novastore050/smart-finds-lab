# Final report — conditional approval, option B (2026-11-03)

Owner decision: **option B**. TP19H stays at #2 and the 3-container Rubbermaid set (B01JCNEJSO) at #10. No switch to
the ATK 10-piece set, because its exact match is not verified. Production has **not** started; it needs your
explicit approval.

## Backups
Exact copies of the approved files, taken before any change, are in
`productions/kitchen-gadgets-10/backup/approved-2026-11-03/`: production.yaml, script.yaml, script.md,
thumbnail-concepts.md, youtube.md, youtube.json and config/studio.yaml. The approved `script/script.yaml` itself is
unchanged.

## The four fixes (before → after)

| # | File | Before | After |
|---|---|---|---|
| 1 | `production.yaml` → SEO title option 2 (also in `seo/youtube.md/.json`) | 10 Kitchen Gadgets People Actually Keep Using | **10 Kitchen Gadgets That Fix Annoying Everyday Jobs** (50 chars) |
| 2 | `production.yaml` → SEO description intro (also in `seo/youtube.md/.json`) | Most kitchen gadgets get used once and forgotten. These 10 fix small, annoying jobs you do every day - from easy eggs and leak-proof leftovers to faster chopping, cleaner dishes and better coffee. For each one: what it does, what buyers like, and the honest downside. | **Plenty of kitchen gadgets end up forgotten in a drawer. These 10 fix small everyday jobs - from one-button boiled eggs and drier salads to faster chopping, cleaner dishes, better coffee and food containers that Rubbermaid sells as leak-proof. This countdown is our editorial selection, based on manufacturer information, expert reviews and buyer feedback - we did not test these products ourselves. For each one: what it does, what buyers like, and the honest downside.** |
| 3 | `config/studio.yaml` → channel research disclaimer (all videos; also in `seo/youtube.md/.json`) | Smart Finds Lab researches products using specifications, verified customer reviews and expert comparisons. We did not physically test these products unless we say so. | **Smart Finds Lab picks products through research: manufacturer information, expert reviews and buyer feedback. We did not physically test or directly compare these products unless we say so. Our rankings are editorial picks, not lab results or sales rankings.** |
| 4 | `production.yaml` thumbnail variant A + `production/thumbnail-concepts.md` concept A | Sub text: Researched & compared | **Sub text: Researched picks** |

Related changes:
- Thumbnail concept B hero image: the Rubbermaid 3-container set (now #10, weakest evidence) → the **TP19H** (#2).
- The same "Researched & compared" text was also the built-in default in `scripts/studio_engine/seo.py`,
  `scripts/studio_engine/pipeline.py` and `docs/EDITING-GUIDE.md`. All three now say "Researched picks".
- `seo/youtube.md` keeps the chapter order of the still-approved original script. The SEO pack for the final
  script is `seo/youtube-final-v2.md`.

## Script corrections in FINAL v2 (`script/review/script-final-v2.yaml/.md`)
- Short 3, before: "Every cut lets the juices run out." After: **"Slicing in to check can let some of those juices
  escape."**
- The same overstatement was in the long-form #2 scene. Before: "Cutting into chicken to check it lets the juices
  run out". After: **"Cutting into chicken to check it can let some of the juices escape"**.
- Disclosure: "…and this isn't a **lab ranking** or a sales chart. The order is our editorial call, based on
  **manufacturer information**, expert reviews and buyer feedback…"
- On-screen subtitles: "Best for:" → "Good for:" (avoids a superlative).
- The SEO description lists the Rubbermaid set without the Amazon title's "Leak-Proof … Airtight" wording.

## Durations (estimates at 155 words/min; the real voice decides)
- Long video narration: **7.7 min**. With the intro sting, transitions and the 12 s end screen: **about 8.1 min**.
- Short 1 (Dash): **~42 s** · Short 2 (Microplane): **~47 s** · Short 3 (TP19H): **~46 s**. At a typical AI-voice
  pace (~165 wpm) that is about 39 / 44 / 43 s.

## Checks
- `tests/test_studio_e2e.py`: **ALL 58 CHECKS PASSED**.
- Script checker on FINAL v2: no testing claims, no prices, no unverified ratings, no copied phrasing. Shorts: same
  checks, plus no references to another video.
- Consistency (`final-consistency.md`): all 10 products, names and ASINs match the description links; all are
  approved products; each Short links to the scene for the same product; affiliate disclosure is both spoken and in
  the description. Ranking-language scan: 0 items needing review.
- Approved `script/script.yaml` checksum unchanged · YAML files parse · secret scan clean.

## Remaining risks
**Factual**
1. No ASIN, title, availability or rating has been verified on the live Amazon.com pages. That is your check before
   publishing.
2. Rubbermaid #10: "leak-proof" is only the maker's claim (said on air). Set contents differ between retailers.
3. Fullstar: the exact blade set for B0764HS4SL is unconfirmed (said on air).
4. Dash capacity: 6 eggs per the manual; one retailer says 7.
5. Some cons come from blogs or review summaries (Dash buzzer, KitchenAid rust). They are attributed as
   "some reviewers/owners".
6. Microplane: confirm the linked US listing shows the protective cover.

**Copyright / licensing**
1. 54 stock clips are planned and none has been chosen. Each needs its own licence check (`stock-license-check-final-v2.md`).
2. Product photos must be your own or used with permission. Amazon listing images can't be used without permission.
3. The existing thumbnail mockups (`thumbnails/*.jpg`, not in git) still show the old "Researched & compared" text.
   They were not regenerated, because that would be image generation. Regenerate them after approval.
4. Music: no track is chosen yet (`production.yaml` → music is empty). Pick a track with a clear commercial licence and record it there before rendering.
5. Commercial use of ElevenLabs audio needs a paid plan. AI clips must stay generic (no copying of real products or
   brands), and YouTube's "altered or synthetic content" box should be ticked if realistic AI scenes are used.
6. Reference channels were used for pacing only. The script passed the 7-word originality check.
