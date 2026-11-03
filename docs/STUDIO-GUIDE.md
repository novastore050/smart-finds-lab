# Production Studio guide (research → finished video)

The studio connects every step of a video:

**Product research → Amazon verification → Script → Scene prompts → Voice-over → Clip import →
FFmpeg editing → 3 Shorts → Thumbnails → SEO → Quality control → your review**

It uses the existing editor (`scripts/sfl.py`), so everything in the other guides still applies.
**Nothing costs money, generates paid media or gets published by itself.** The steps that need you
are marked 👤.

Each video lives in its own folder:

```
productions/<video-name>/
  production.yaml        settings + progress (which steps are done)
  research/              products.yaml, report.md, shortlist.md, amazon-verification.csv
  script/                script.yaml (edit this), script.md (easy to read)
  prompts/               higgsfield-prompts.md, shotlist.csv
  voice/                 text per scene, voice files, word timings, exact subtitles
  edit/                  timeline.yaml + shorts.yaml (generated for the editor)
  thumbnails/            thumbnail variants
  seo/                   youtube.md (titles, description, chapters, tags)
  reports/               production-qc.md (final quality report)
```

See where any video stands, and the exact next command, with:

```bash
python scripts/studio.py status kitchen-gadgets-10
```

---

## 1. Start a video

```bash
python scripts/studio.py new "7 Cleaning Gadgets Worth Buying" --slug cleaning-gadgets-7
```

In `productions/<name>/production.yaml` set `products_wanted`, `topic_noun` (e.g. `cleaning gadgets`) and
`music: {file: assets/music/your-track.mp3, license: "where it is from"}`.
Add `--hands-on` only if you will really test the products yourself.

## 2. Research (Claude does this)

Ask Claude Code (the `youtube-studio` skill): *"Research 7 cleaning gadgets for cleaning-gadgets-7"*.
Claude searches the web and writes `research/products.yaml`. Every value has its source and date and is
marked **unverified** until checked on Amazon. Then:

```bash
python scripts/studio.py research-report cleaning-gadgets-7
```

Read `research/shortlist.md` (ranked list) and `research/report.md` (all details + sources).

## 3. 👤 Verify on Amazon and approve

Open `research/amazon-verification.csv` (Excel / Google Sheets), open each link on Amazon.com, and fill
in: correct product? available in US? current price, star rating, number of ratings, ASIN, and the date
you checked. Save as CSV, then:

```bash
python scripts/studio.py import-verification cleaning-gadgets-7
```

Answering "no" for correct product or availability rejects that product (replace it with a reserve).
When you are happy with the list:

```bash
python scripts/studio.py approve-products cleaning-gadgets-7
```

Nothing after this point runs before approval.

## 4. Script

```bash
python scripts/studio.py draft-script cleaning-gadgets-7
```

This writes an honest first draft from the research. Ask Claude to polish it, or edit
`script/script.yaml` yourself, then check it:

```bash
python scripts/studio.py check-script cleaning-gadgets-7
```

The checker blocks:
- testing claims in research-based videos
- prices in the narration
- star ratings that are not verified
- phrases copied from reference channels

It also estimates the length of each scene.

## 5. Scene prompts (Higgsfield, manual)

```bash
python scripts/studio.py prompts cleaning-gadgets-7
```

Open `prompts/higgsfield-prompts.md`. It has one prompt per shot, organised by scene, with the aspect
ratio, length and the file name to save as (e.g. `s03-a.mp4`). Scenes used in Shorts also get a vertical
version (`s03-a-v.mp4`). The `-photo` shots are your real product photos.

👤 Generate the clips on higgsfield.ai, download them, then copy them in:

```bash
python scripts/studio.py import-clips cleaning-gadgets-7 "C:\Users\you\Downloads\higgsfield"
```

Only files whose names contain the shot id are imported; your downloads are never changed.

## 6. Voice-over (ElevenLabs)

```bash
python scripts/studio.py voice-pack cleaning-gadgets-7
```

This creates one text file per scene and shows the number of characters, which is what ElevenLabs
charges for. See [VOICE-ELEVENLABS.md](VOICE-ELEVENLABS.md) for the three ways to generate. 👤 You
approve any spending. Then import the files and create exact subtitles:

```bash
python scripts/studio.py import-voice cleaning-gadgets-7 "C:\Users\you\Downloads\voice"
```
```bash
python scripts/studio.py align cleaning-gadgets-7
```

## 7. Render everything

```bash
python scripts/studio.py render cleaning-gadgets-7
```

This makes:
- the long video → `output/long-videos/`
- 3 Shorts → `output/shorts/`
- 2 thumbnails
- the SEO pack → `seo/youtube.md`
- the final QC report → `reports/production-qc.md`

Preview options: `--draft` (fast) and `--placeholders` (title cards where clips are still missing).

## 8. 👤 Review and upload

Open `reports/production-qc.md`:
- **Part A** is what the computer measured.
- **Part B** is your checklist. Only a person can judge it.

When Part B is done:

```bash
python scripts/studio.py review-done cleaning-gadgets-7
```

Then upload manually in YouTube Studio. Copy the title, description, tags and chapters from
`seo/youtube.md`, and upload the `.srt` file as captions.

---

## Reference channels (inspiration, never copying)

```bash
python scripts/studio.py reference-new kitchen-ref --channel https://www.youtube.com/@SomeChannel --video https://www.youtube.com/watch?v=XXXXXXXXXXX
```

1. Fill in `references/kitchen-ref/reference.yaml`: titles, dates, lengths, views and descriptions.
2. Optionally, paste transcripts into `references/kitchen-ref/transcripts/<video_id>.txt`. They stay on
   your computer and are never uploaded to GitHub.
3. Run the analysis:

```bash
python scripts/studio.py reference-analyze kitchen-ref
```

The report labels what is measured from data (📊 📝 🎞️) and what needs your eyes (👁️). Scripts are
automatically checked against the transcripts, so wording is never copied.

Optional: with a free YouTube Data API key stored in the environment variable `YOUTUBE_API_KEY`,
`reference-fetch` fills in the metadata for you. Not needed otherwise.

## Settings files

| File | What it controls |
|---|---|
| `config/studio.yaml` | Words per minute, disclosures, visual style for AI prompts, SEO tags, Amazon tag |
| `config/voice.yaml` | The channel voice (same for every video) and pronunciation fixes |
| `config/brand.yaml` | Colours, fonts, titles, subtitles, music level (editor) |

## Testing the system

```bash
python scripts/sfl.py make-test-media
```
```bash
python tests/test_studio_e2e.py
```

This runs the whole pipeline with fictional products and placeholder media. It should finish with
`ALL … CHECKS PASSED`.
