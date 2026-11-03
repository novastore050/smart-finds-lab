# Report: editor changes + promotion of script-final-v2 (2026-11-03)

Scope approved by the owner: **step 1 (editor changes) and step 2 (promote the final script) only.** No audio,
images or videos were generated with AI. No credits were spent, nothing was downloaded or bought, and nothing was
published. No backup or old file was deleted. Passing tests prove that the **software** works. They prove nothing
about the accuracy of the product information or the rights to use any media.

## 1. Editor changes (step 1)

| Feature | What it does | Files |
|---|---|---|
| Standalone Shorts audio | A Short with its own `narration` gets its own voice file (`voice/short1.mp3` …), its own vertical shots and its own ending. The "Full top 10 on the channel" CTA is now used only by old-style Shorts. `voice-pack`, `import-voice`, `align`, `tts` and QC include the Shorts. `check-script` checks Short narration too (no testing claims, prices, ratings, ranks or references to the long video). | `studio_engine/script.py`, `voice.py`, `timeline.py`, `prompts.py`, `package.py`, `production_qc.py` |
| Graphic cards | New `graphic` shot type: `pros_cons`, `spec`, `disclosure`, `halfway`, `recap`, `note`, `cta`. Drawn by the existing ASS graphics engine over the brand gradient. The pros/cons labels are the neutral **"THE GOOD / THE CATCH"**, because some points are manufacturer facts, not buyer opinions. Graphic shots are never reported as "missing" and never sent to Higgsfield. | `sfl_engine/config.py`, `plan.py`, `graphics.py`; `studio_engine/timeline.py` |
| Per-photo camera moves | Each `product_photo` shot keeps its own `motion` (zoom in/out, pan) and `crop`. `full` shows the whole product; any other crop gives a closer detail framing (zoom 1.35 around `focus_x`/`focus_y`). | `sfl_engine/config.py`, `render.py`, `plan.py` (cache key); `studio_engine/timeline.py` |
| SEO pack fixes | (1) `production.yaml → seo.display_names`: the Rubbermaid set is listed without the Amazon title's "Leak-Proof … Airtight". (2) Standalone Shorts' descriptions read "Research-based: we did not test this product ourselves." instead of "part of our …". | `studio_engine/seo.py` |
| Extra guards | `withdrawn_claims` in production.yaml (blocked by `check-script`). QC flags voice files recorded from older script text, and a timeline built from a different script version (the timeline stores the script's md5). `prompts` now lists stock clips as stock (not AI) and skips graphic cards. `build-timeline` and `seo` now update their stage status. | `script.py`, `voice.py`, `production_qc.py`, `prompts.py`, `studio.py` |

Each feature has its own independent test: `tests/test_editor_features.py` (50 checks, fictional data and
placeholder files only; renders go to `temp/`).

## 2. Promotion (step 2)

- `script/review/script-final-v2.yaml` (md5 `98f7e0c9…`, **unchanged**) was copied to `script/script.yaml` (md5
  `220bf451…`). The only changes are the 3 stock searches below, plus the `status` and `promoted_from` fields.

  | Shot | Before | After |
  |---|---|---|
  | s03-d | meal prep containers refrigerator | leftovers glass bowls fridge shelf |
  | s05-h | hand washing drying scissors kitchen towel | hands drying utensil kitchen towel |
  | s07-e | washing wine glass brush sink | rinsing wine glass under tap by hand |

- The previous approved script is kept in three places: `backup/approved-2026-11-03/`,
  `superseded/2026-11-03-pre-final-v2/script/` and git history.
- Regenerated from the promoted script: `script/script.md`, `voice/text/*` (13 scenes + short1–3),
  `voice/voice-jobs.json`, `voice/README.md`, `prompts/*`, `production/visual-plan.md`, `edit/timeline.yaml`,
  `edit/shorts.yaml`, `production/shorts-scripts.md`, `voiceover-sections.md`, `thumbnail-concepts.md`
  (heroes: #1 Dash, #2 TP19H), `production-checklist.md`, `README.md`, `seo/youtube.md/.json`,
  `reports/production-qc.md`.
- Older proposal plans that still mention withdrawn claims were moved to
  `superseded/2026-11-03-pre-final-v2/proposal-history/`.
- `production.yaml`: `script_source`, `withdrawn_claims` (14 phrases) and `seo.display_names` added. Stages
  refreshed: script, prompts, timeline ("placeholder preview"), seo ("chapters estimated"), qc. The **thumbnail**
  stage was removed because the old mockups are superseded and new ones are not made yet.

## 3. Evidence that the pipeline reads V2

- Every command (`voice-pack`, `prompts`, `plan`, `build-timeline`, `render`, `seo`, `package`, `qc`, `tts`)
  loads `script/script.yaml`, which is now V2. No code reads `superseded/` (grep: 0 matches).
- Narration in `script/script.yaml` is identical to V2 for all 13 scenes and 3 Shorts, and identical to the old
  script in **0 of 13** scenes.
- `edit/timeline.yaml → source_script_md5` = md5 of `script/script.yaml` (QC: "timeline matches the current
  script").
- All 16 `voice/text/*.txt` files equal the V2 narration (with pronunciation fixes).
- V2-only phrases found in the regenerated files: "Number ten is a Rubbermaid" (s03.txt, timeline, script.md);
  "Slicing in to check can let some of those juices escape" (short3.txt, shorts.yaml); "If your lemon zest tastes
  bitter" (short2.txt, shorts.yaml).

## 4. voice/text/s11.txt

Now: *"Number two. Cutting into chicken to check it can let some of the juices escape … The T P nineteen H
instant-read thermometer …"*. No Rubbermaid mention, and **0 of the 14 withdrawn phrases**. The old file
(`superseded/…/voice/text/s11.txt`) contains 8 of them: America's Test Kitchen, won its plastic, lids aren't sold
separately, tomato sauce can stain, cracked lids or broken latches, no water got out, Number two: Rubbermaid, …. A
scan of all 47 active production files found **no** withdrawn phrase.

## 5. Placeholder production test (no real media)

Rendered from the promoted script with `--placeholders` (missing clips, photos and voice → branded cards; graphic
cards drawn). Output in `temp/placeholder-test/` (not `output/`, not in git). No thumbnails made.

| Video | Size | Length | Ending | Render QC |
|---|---|---|---|---|
| Long video | 1920×1080 | 8:00 (estimated timing, no voice) | outro card | PASS WITH WARNINGS |
| Short 1 — This Egg Cooker Shuts Itself Off | 1080×1920 | 43.2 s | "Comment · Subscribe" | PASS WITH WARNINGS |
| Short 2 — Why Your Lemon Zest Tastes Bitter | 1080×1920 | 47.8 s | "Comment · Subscribe" | PASS WITH WARNINGS |
| Short 3 — Stop Guessing When Chicken Is Done | 1080×1920 | 47.5 s | "Subscribe" | PASS WITH WARNINGS |

The warnings are expected for a placeholder build (no voice, so low loudness; "media missing" cards). 95 items not
imported (voice, photos, AI and stock clips). Frames checked by eye: pros/cons card (THE GOOD / THE CATCH),
disclosure card, Shorts lower third and captions.

## 6. Tests

- `tests/test_studio_e2e.py`: **ALL 58 CHECKS PASSED**
- `tests/test_editor_features.py`: **ALL 50 FEATURE CHECKS PASSED**
- `studio.py check-script kitchen-gadgets-10`: **OK** (13 scenes + 3 standalone Shorts, withdrawn-claims guard
  active)
- `studio.py qc kitchen-gadgets-10 --fast`: FAIL, as expected before production. Its 7 errors are exactly the
  missing assets: voice (16 files), 105 shots, long video, 3 Shorts, thumbnail. The timeline and script checks pass.
- `script-final-v2.yaml` and `backup/` unchanged (git diff clean) · secret scan clean.

## 7. Still needed before the first real scene

1. **Your live Amazon checks** (`preproduction/product-verification.csv`), especially the Rubbermaid set contents,
   the PowerLix Deep Blue ASIN and the KitchenAid "listed as dishwasher safe" wording.
2. **Product photos** with clear rights (your own, or written permission from the maker). None exist yet.
3. **Voice approval:** ElevenLabs, voice Aabo, 8,673 characters for 13 scenes + 3 Shorts (1 take), plus a paid plan
   for commercial use. The Zulay pronunciation is still a guess.
4. **Music** (none chosen) and **stock clips** (54, licence check on download).
5. **AI clips:** 28 clips, credit approval needed (980 credits at 720p / 2,240 at 1080p).
6. **Visual review:** only a few graphic-card frames were checked by eye. Watch the first real draft for text
   size and line breaks on all 24 cards.
7. Thumbnails must be made again from the corrected text (not done: no images in this step).
8. Chapter times stay estimates until the real voice files are imported.
