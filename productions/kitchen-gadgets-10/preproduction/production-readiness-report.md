# Production readiness report — kitchen-gadgets-10 (FINAL v2, option B)

Prepared 2026-11-03. **Verdict: NOT READY to start production.** The editorial content is ready. The blockers are
asset rights, live Amazon checks, owner decisions about spending, and four editor changes that the final script
needs. Nothing has been generated, downloaded, bought or published. `script-final-v2` and the backups were not
touched.

## 1. Status at a glance

| Area | Status | Details |
|---|---|---|
| Script (long + 3 Shorts) | ✅ Editorially approved (conditional) | `script/review/script-final-v2.yaml`. Narration ~7.7 min (~8:05 with intro sting, transitions and end screen). Shorts ~42 / 47 / 46 s at 155 wpm (~39 / 44 / 43 s at a typical AI-voice pace). |
| Amazon products | ⛔ Not live-verified | amazon.com is blocked here. 7 of 10 are "likely" matches from indexed data, 3 are not confirmed (PowerLix ASIN↔Deep Blue, Fullstar model, Rubbermaid set contents). See `product-verification.csv`. |
| Product images | ⛔ None licensed | Your own photos, or manufacturer images with written permission. Amazon images are not allowed. |
| Stock footage (54 clips) | ⚠️ Planned, none chosen | 35 OK, 16 allowed only if a stated condition holds, 3 swapped for safer shots. Each clip needs its licence saved on download day. |
| AI clips (28) | ⛔ Not approved | 980 credits at 720p / 2,240 at 1080p; the account has 10 credits. |
| Voice-over | ⛔ Not approved | ~9,402 ElevenLabs credits (1 take); commercial use needs a paid plan. |
| Music | ⛔ None chosen | Recommended: YouTube Audio Library, "Attribution not required" (`music-options.md`). |
| SFX, fonts, brand intro/outro | ✅ | Our own generated SFX; Inter (OFL). |
| Editor/pipeline support for the final plan | ⛔ 4 gaps | See §3. |

## 2. Production file consistency (the checks you asked for)

| Check | Result | What was done / what is needed |
|---|---|---|
| Pipeline uses `script-final-v2` | ❌ **Not yet.** Every studio command (`voice-pack`, `prompts`, `build-timeline`, `render`, `seo`, `qc`) reads `script/script.yaml`, which is still the old approved script. | **Promotion step (needs your OK):** copy `script/review/script-final-v2.yaml` → `script/script.yaml`. The original is backed up in `backup/approved-2026-11-03/`. At the same time, apply the 3 stock-search replacements from `stock-footage-manifest.csv` (REPLACE rows) to the promoted copy. `script-final-v2` itself stays unchanged. |
| SEO package = `seo/youtube-final-v2.md` | ⚠️ `youtube-final-v2.md` is the reference pack (estimated chapters). On render, `seo.build` regenerates `seo/youtube.md` from the promoted script plus real chapter times. | Two small differences must be added to `seo.build` first (§3.4): the Rubbermaid display name without "Leak-Proof … Airtight", and the Shorts descriptions with the research note instead of "part of our …". Then compare the generated pack against `youtube-final-v2.md` before upload. |
| Old chapter times / descriptions can't overwrite the final | ✅ **Done today.** Every file generated from the old script was moved to `superseded/2026-11-03-pre-final-v2/` (with a README). | Moved: `edit/timeline.yaml`, `edit/shorts.yaml` (old chapter basis and old Shorts CTA); `voice/text/s01–s13.txt` + `voice-jobs.json` (**old narration with the withdrawn Rubbermaid/ATK claims**); old `prompts/`; old `seo/youtube.md/.json`; old `shorts-scripts.md`, `voiceover-sections.md`, `visual-plan.md`. Nothing deleted. |
| Old thumbnail text not used | ✅ | Thumbnails are rendered from `production.yaml → thumbnail.variants`, which now say "Researched picks". The old mockup JPGs ("Researched & compared") were moved to `superseded/…/thumbnails/` (local only, git-ignored). The built-in default text was also fixed earlier. |
| All three Shorts use their dedicated final scripts | ❌ **Not yet.** The editor builds Shorts by cutting the long-video scene (`use_scenes`) with the long-video audio, and adds the CTA "Full top 10 on the channel". That breaks the standalone-Short requirement. | Editor change §3.1. |

## 3. Editor changes needed before rendering (code, not media; your approval needed)

1. **Dedicated Shorts.** Use each Short's own `narration` and `shots`, with voice files `voice/short1.mp3 …
   short3.mp3`. Drop the "Full top 10 on the channel" CTA in favour of the Short's own ending, and include the
   Shorts in `voice-pack` / `align`.
2. **`graphic` shots** (pros/cons, spec, halfway, recap, disclosure, CTA cards; 15 long + 9 Shorts). Today they
   would be reported as missing clips. Render them with the existing ASS graphics engine.
3. **Product-photo `motion` / `crop`.** The editor currently uses one zoom-in for every photo. The plan uses two
   different moves per product. Honour the per-shot settings.
4. **SEO pack.** Per-product display names (production.yaml) and the research note in the Shorts descriptions, to
   match `youtube-final-v2.md`.

`stock` shots already work: save each chosen clip as `assets/video/kitchen-gadgets-10/<shot-id>.mp4`.

## 4. Remaining factual issues

| Product | Issue | Owner action |
|---|---|---|
| All | No live Amazon check (availability, title, colour, ASIN) | Open each URL in `product-verification.csv` and fill in the owner columns |
| #10 Rubbermaid | Set contents conflict (2 × 1.3 + 1 × 3.2 cup vs other sizes); script says "three clear containers" | Confirm 3 containers / 6 pieces on the live page |
| #5 PowerLix | B08CVPQJHJ not tied to Deep Blue in this check | Confirm colour and that the stand is included |
| #4 Fullstar | Model TF1096C-8 and the blade set unconfirmed (script tells viewers to check) | Confirm the blades listed |
| #8 KitchenAid | "Listed as dishwasher safe" must appear on the linked listing | Confirm, or reword that line before recording |
| #2 TP19H | Listing says 1 s; script uses the manual's 3–4 s (intentional). Colour of the ASIN unknown | Match the photo colour to the ASIN |
| #1 Dash | One owner review says "no auto-shutoff"; the manufacturer manual confirms automatic shut-off (the buzzer keeps sounding until pressed). Script is correct. | None |
| #7 Microplane | Cover confirmed by the maker and a retailer | Check the listing photos show it |

## 5. Remaining copyright / licensing risks

1. **Product images:** none licensed yet. This is the biggest blocker. Never use Amazon listing images.
2. **Stock:** free licences don't clear trademarks or identifiable people. 16 clips have conditions (no logos, no
   other brand's gadget, no faces); 3 searches were replaced. Save each licence when downloading.
3. **Music:** none chosen. Avoid Pixabay tracks marked Content ID, any CC BY-NC track, and Uppbeat without its
   credit line.
4. **AI clips:** generic only; never imitate the products or show unverified results. Tick YouTube's
   altered/synthetic content box if realistic.
5. **Voice:** commercial use of ElevenLabs output needs a paid plan.
6. **Licence pages:** Pexels, Pixabay, Mixkit, Coverr, Uppbeat and the YouTube Audio Library couldn't be opened
   from here. The terms are summarised from search results; re-read them when you download.

## 6. Suggested order once you approve

1. Live Amazon checks → fill in `product-verification.csv`.
2. Product photos (own or permitted) → `assets/images/kitchen-gadgets-10/`.
3. Approve the editor changes (§3) → I implement and test them (no media needed).
4. Approve the promotion of `script-final-v2` → regenerate voice pack, prompts, timeline and SEO from it.
5. Approve spending (voice, then AI clips) → generate → import.
6. Choose stock clips and music, with licences saved.
7. Draft render → QC report → your review → final render → manual upload.

## 7. Tests run

- `tests/test_studio_e2e.py`: **ALL 58 CHECKS PASSED**.
- `studio.py check-script` (approved script): OK. FINAL v2 checks: no testing claims, prices or unverified ratings (run in the previous step; file unchanged since).
- Approved `script/script.yaml` checksum unchanged; `script-final-v2` and `backup/` unchanged (git diff clean).
- Secret scan of all new or changed files: clean.
- No preproduction file contains downloaded media; nothing was generated or bought.
