# Reference channel analysis

1. `studio.py reference-new <name> --channel https://www.youtube.com/@channel --video <url> --video <url>`
   creates `references/<name>/reference.yaml`, `transcripts/` and a README.
2. Fill metadata: the owner pastes title, published date, duration, views and description for each video
   (or, optionally, `YOUTUBE_API_KEY` in the environment + `studio.py reference-fetch <name>`).
   In cloud sessions youtube.com is usually blocked, so don't promise to fetch pages.
3. Optional transcripts: YouTube → "…" → Show transcript → copy → `transcripts/<video_id>.txt`
   (timestamps allowed). Kept out of git.
4. Optional local video file the owner may analyse: `--video-file path` measures cuts/min, average shot
   length, brightness and saturation with FFmpeg.
5. `studio.py reference-analyze <name>` → `references/<name>/report.md` + `analysis.json`.

The report labels every section: 📊 metadata, 📝 transcripts, 🎞️ measured from a local file,
👁️ needs manual visual review (visual style, on-screen text, b-roll, thumbnails, music, editing feel —
the owner writes these into `manual_observations`). Never present the 👁️ items as analysed by software.

Use findings as targets (hook length, pacing, chapter structure, title patterns). Never reuse wording;
`check-script` compares every script against the transcripts (7-word matches = error).
