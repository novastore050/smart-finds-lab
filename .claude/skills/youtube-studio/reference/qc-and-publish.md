# Render, QC and hand-off (stages 9–11)

`studio.py render <slug>`:
1. `build-timeline` → `edit/timeline.yaml` + `edit/shorts.yaml` (ordinary timelines for `sfl.py`).
2. Long video → `output/long-videos/<slug>.mp4` (+ `.srt`, `.qc.md`).
3. 3 Shorts → `output/shorts/<slug>-short-1..3.mp4`.
4. Thumbnails → `productions/<slug>/thumbnails/<slug>-a.jpg`, `-b.jpg` (1280×720).
5. SEO → `seo/youtube.md` + `.json` (titles, description with chapters + links + disclosures, tags, Shorts
   metadata, pinned comment). Chapters come from the real edit plan; warns if estimated or dropped.
6. Final QC → `reports/production-qc.md`.

Previews: `--draft` (fast encode), `--placeholders` (title cards instead of missing clips).

## Final QC report

Part A (automated): research validity + approval + verification status, script checks, voice/clips present,
word-level subtitle coverage, render QC (resolution, codecs, fps, duration, A/V sync, black frames,
silence, loudness), full-decode export integrity, thumbnails (1280×720, < 2 MB), SEO rules (disclosure,
≤ 100-char titles, ≤ 5000-char description, valid chapters, links), secret scan.

Part B (human, never auto-ticked): watch the video, accuracy of names/text, AI b-roll honesty, voice,
subtitles, Shorts framing, thumbnail, links/prices, licences, YouTube settings. Owner then runs
`studio.py review-done <slug>`.

## Before every git commit

```bash
git status --short
python -c "import sys; sys.path.insert(0,'scripts'); from pathlib import Path; from studio_engine.production_qc import scan_secrets; print(scan_secrets([Path('.')]) or 'no secrets found')"
```
`.gitignore` keeps out: rendered videos, temp/, logs/, voice previews, reference transcripts, test
productions (`zz-*`), `.env`. Never commit API keys, `.env` files or licensed media.
