# First real scene plan — s01 Hook (≈13–14 s)

Prepared 2026-11-04. **Plan only:** no voice generated, no clips generated or downloaded, no credits spent, nothing
published. Test timeline (placeholders, current state): `edit/scene-s01.yaml`. Rebuild it any time with
`python scripts/studio.py build-timeline kitchen-gadgets-10 --only s01`.

## Why s01

- It is the 13–14 s scene viewers see first. It sets the voice, pace and look for the whole channel.
- It has no product claims, no product photo and no difficult brand names, so the first real test is about voice,
  picture, motion and subtitles only.
- Second choice if you prefer to test a product scene: the first ~14 s of s11 (#2 TP19H). That one needs a licensed
  product photo first.

## 1. Voice

| Item | Value |
|---|---|
| Text (subtitles / on screen) | Plenty of kitchen gadgets end up forgotten in a drawer. These ten fix jobs you actually do, and number one turns a breakfast you usually have to babysit into a one-button job. |
| Text sent to the voice | identical (`voice/text/s01.txt`; no names need a pronunciation fix in this scene) |
| Voice / model | Aabo `KeU8nqWFDbaoi0QVUjD3` · `eleven_multilingual_v2` · `mp3_44100_128` |
| Settings | stability 0.50 · similarity 0.75 · style 0 · speaker boost on · speed 1.0 (`config/voice.yaml`, status: chosen) |
| Length | ~12.8 s spoken (estimate at 155 wpm) → scene ≈ 13.4–13.8 s with the editor's 0.15 s lead-in and 0.45 s tail |
| Cost | **175 characters = 175 credits ≈ $0.02**, 1 take. It must be generated **while a paid plan is active** (commercial licence); Starter is listed at about $5–6/month. |
| Delivery | Confident and warm. Slight pause after "drawer." Lift on "number one". End firmly on "one-button job." |
| Save as | `voice/s01.mp3` → `python scripts/studio.py import-voice kitchen-gadgets-10 <folder>` (the file name must contain `s01`) |

**Subtitle timing, pick one:**
- **Exact (recommended):** generate with word timestamps (`python scripts/studio.py tts kitchen-gadgets-10 --scene
  s01 --confirm-spend`, needs `ELEVENLABS_API_KEY` on your PC). This writes `voice/s01.words.json`, then
  `align` → `voice/s01.srt`. The ElevenLabs API host is not reachable from this cloud environment, so this step runs
  on your computer.
- **Simple:** generate on elevenlabs.io and import only the MP3. The editor times the subtitles from the script
  text. Good enough for a test; it may drift by a few tenths of a second.
- Either way, subtitles use the **original spelling**. `align` puts Zulay / TP19H / Microplane back if the voice
  text used the pronunciation spelling.

## 2. Picture (4 shots) — proposed order follows the narration

The approved script currently lists the shots as drawer → egg cooker → boiling pot → counter. In that order the
egg-cooker "solution" shot appears **before** the promise is spoken. I propose this order instead. **It needs your
OK, because it changes `script/script.yaml`.** Nothing has been changed yet.

| Time (est.) | Narration | Shot | Source | What we see | Camera / motion | Rights / rules |
|---|---|---|---|---|---|---|
| 0.0–4.0 | "Plenty of kitchen gadgets end up forgotten in a drawer." | `s01-a` | 🎬 AI (Higgsfield, 5 s, use 4 s) | a cluttered kitchen drawer of unused gadgets, a hand closing it | slow push-in, eye level | generic gadgets only, no logos or readable brands |
| 4.0–6.7 | "These ten fix jobs you actually do," | `s01-d` | 🎞️ stock (Pexels / Pixabay / Coverr) | bright empty kitchen counter in morning light | gentle slide or static | manifest status **OK**; no appliance logos |
| 6.7–10.3 | "and number one turns a breakfast you usually have to babysit" | `s01-c` | 🎞️ stock | eggs boiling in a pot on a stove (the chore) | static or slow push | manifest status **CAUTION**: no brand on the stove, timer or pot |
| 10.3–13.6 | "into a one-button job." | `s01-b` | 🎬 AI (5 s, use 3.3 s) | steam rising as a clear dome lid lifts off a small countertop egg cooker | close-up | **generic** cooker, no logo. It must not copy the Dash design; the real product is shown later with its photo in s12 |

Shot lengths in the script would become: a 4.0 · d 2.7 · c 3.6 · b 3.3 (= 13.6 s). The editor trims or holds to
the real voice length. Fit: AI clips are 16:9 (no crop); stock is chosen in 16:9 at ≥1080p.

**Lower-cost alternative (no AI credits):** replace `s01-a` with a stock "messy kitchen drawer" clip. For `s01-b`,
use the licensed Dash product photo (zoom-in), once you have one. Never use a stock clip that shows a branded egg
cooker.

## 3. Motion, transitions, text

- **Into the scene:** cut (first scene). **Between shots:** straight cuts on the sentence breaks above.
- **After s01** (full video only): the 2.6 s brand intro sting, then the disclosure scene.
- **Title overlay:** "10 Kitchen Gadgets That Actually Make Life Easier", 0.4–3.9 s, with the pop sound.
  - Check that the title doesn't collide with the first subtitle line. If it does, start the subtitles at 0.8 s or
    shorten the title display.
- **Watermark:** "SMART FINDS LAB", top-right, 55 % opacity.
- **Subtitles (long-form style):** bottom, white on a 45 % black box, 44 px, max 42 characters × 2 lines. Expected
  cues:
  1. "Plenty of kitchen gadgets end up forgotten in a drawer."
  2. "These ten fix jobs you actually do, and number one turns…"
  3. "…a breakfast you usually have to babysit into a one-button job."

## 4. Sound

- Voice cleaned and levelled. Whole mix normalised to −14 LUFS, true peak ≤ −1.5 dBTP.
- **Music:** none chosen yet. Either test without music, or pick one YouTube Audio Library track ("Attribution not
  required"). It plays at −19 dB and ducks under the voice.
- **SFX:** pop on the title (our own generated sound). No whoosh, since the first scene starts with a cut.

## 5. Cost of the first scene

| Item | Credits | Money |
|---|---|---|
| Voice s01 (1 take) | 175 ElevenLabs credits | ≈ $0.02, plus a paid ElevenLabs plan for commercial rights |
| 2 AI clips (`s01-a`, `s01-b`) | 70 Higgsfield credits at 720p / 160 at 1080p | needs a Higgsfield plan or credit purchase (account has 10 credits) |
| 2 stock clips (`s01-c`, `s01-d`) | 0 | free if the licence check passes |
| Render | 0 | local FFmpeg |

## 6. Steps once you approve (each step needs your OK)

1. **Decide** the shot order (§2) and whether to use AI or the lower-cost alternative.
2. **Voice:** generate `s01` once on a paid ElevenLabs plan → `import-voice` (→ `align` if word timings exist).
3. **Stock:** pick the 2 clips and record URL, licence and checks in `preproduction/stock-footage-manifest.csv` →
   save as `s01-c.mp4` / `s01-d.mp4` → `import-clips`.
4. **AI:** generate `s01-a`, `s01-b` from `prompts/higgsfield-prompts.md` → `import-clips`.
5. `python scripts/studio.py build-timeline kitchen-gadgets-10 --only s01`
6. `python scripts/sfl.py check productions/kitchen-gadgets-10/edit/scene-s01.yaml`, then
   `python scripts/sfl.py build productions/kitchen-gadgets-10/edit/scene-s01.yaml --draft`.
   Watch it, then build without `--draft`.

**Acceptance check for the first scene:**
- Voice sounds like the test and the names are right.
- Every shot matches its sentence.
- No logos and no look-alike egg cooker.
- Title and subtitles readable, with no overlap.
- Loudness −14 LUFS (±1).
- Length 10–15 s.
- Render QC PASS (warnings reviewed).
