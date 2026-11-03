# Using Higgsfield AI clips

**The editing system does not depend on Higgsfield.** It edits any video files you put in
`assets/video/`. Higgsfield is just one possible source of clips.

## With the Production Studio (recommended)

1. Generate prompts. They are organised by scene, with the file name to save each clip as:

```bash
python scripts/studio.py prompts <video>
```

2. Open `productions/<video>/prompts/higgsfield-prompts.md`.
3. Generate each shot on higgsfield.ai.
4. Download the clips. Keep the shot id (e.g. `s03-a`) in each file name.
5. Copy them into the project:

```bash
python scripts/studio.py import-clips <video> "PATH/TO/DOWNLOADS"
```

Status checked on 2026-11-03: the connected Higgsfield account is on the **free plan with 10 credits**.
One 5-second 1080p clip (Seedance 2.5) costs **80 credits**, so automated generation isn't possible
without buying credits. Claude will never generate or spend credits without your explicit OK.

## Older workflow (works today, no API needed)

1. Generate clips on higgsfield.ai.
   - For Shorts, generate **9:16** versions; for the long video, **16:9**. (Either works in both:
     the system reframes, but native framing looks best.)
   - Ask for 1080p where available; 5–8 s clips are ideal.
2. Download them into any folder, e.g. `Downloads/higgsfield-kitchen`.
3. Copy them into the project (your downloads are **not** changed or moved):

```bash
python scripts/sfl.py import-clips "C:\Users\YOU\Downloads\higgsfield-kitchen" --to kitchen-gadgets-10 --prefix hf
```

   This gives the files clean names, never overwrites an existing file, and writes
   `assets/video/kitchen-gadgets-10/manifest.csv` with each clip's resolution, aspect ratio, length
   and notes (e.g. "below 1080p").
4. Put the new file names into your timeline under `clips:` (the command prints ready-to-paste lines).
5. Run `check`. It flags low-resolution clips and aspect ratios that will be reframed.

## Higgsfield integration options (as researched on 2 Nov 2026)

| Option | Status | What it means |
|---|---|---|
| **Manual download + `import-clips`** | ✅ Built and tested | The supported way. Fully works. |
| **Higgsfield developer API** | ⚠️ Exists, not wired in | Higgsfield offers a paid REST API with Python/TypeScript SDKs (docs at docs.higgsfield.ai). It is billed separately from a higgsfield.ai subscription (pay-as-you-go, $5 minimum top-up, priced per second of video). I could not open the API docs from the build environment, so no API code was written: it would have been guesswork. |
| **Higgsfield connector in Claude** | ℹ️ Available in Claude | Claude sessions with the Higgsfield connector enabled can generate clips on your Higgsfield account (this uses your credits). The clips are then downloaded and imported as above. Not used during this build because it spends credits. |

### If you want direct API automation later
1. Create an API key in Higgsfield's developer console (see docs.higgsfield.ai for the current URL) and add credit.
2. Keep the key out of the project files: store it in an environment variable such as `HIGGSFIELD_API_KEY`.
3. A small `scripts/sfl_engine/higgsfield_api.py` could then: send a prompt (or a product image) →
   wait for the job → download the MP4 into a staging folder → call the existing `import_clips()`.
   The rest of the pipeline does not change.

Ask for this when you're ready, with API access active, so it can be built against the real
documentation and tested with one cheap generation.

## Notes on AI clips for product reviews
- AI-generated footage must not **misrepresent** a real product (wrong shape, features it doesn't
  have). Use it for mood/b-roll (hands chopping, kitchen scenes) and use real product photos for the product itself.
- YouTube requires you to tick **"Altered or synthetic content"** when realistic AI footage could be
  mistaken for real events or people. Check the current YouTube policy when uploading.
