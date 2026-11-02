# Editing guide: making a new video, step by step

## The idea in one minute

A video is a list of **scenes**. Each scene has:

- **clips**: video files and/or photos shown in that scene
- **voice**: the voice-over for that scene (one audio file per scene is easiest)
- **narration**: the words spoken (used for subtitles if you don't have an `.srt`)
- **overlays**: on-screen graphics (badge `#3`, product-name lower third, callout…)

**The voice sets the scene length.** If the voice for product #3 lasts 24 seconds, the scene
lasts about 24 seconds, and the clips are trimmed or repeated to fit. So you don't need to
calculate timings.

The system automatically adds the intro sting, transitions, background music (quieter while you
speak), sound effects, subtitles, watermark, end screen, and a quality-control report.

---

## Step 1: Create the timeline

```bash
python scripts/sfl.py new "7 Cleaning Gadgets Worth Buying" --products 7
```

This creates `config/timelines/7-cleaning-gadgets-worth-buying.yaml` and empty folders:

```
assets/video/7-cleaning-gadgets-worth-buying/
assets/audio/7-cleaning-gadgets-worth-buying/
assets/images/7-cleaning-gadgets-worth-buying/
```

## Step 2: Write the script and record the voice-over

Write one short paragraph per scene (hook, each product, wrap-up). Record or generate **one audio
file per scene** and name them like the timeline expects: `00_hook.mp3`, `07.mp3` … `01.mp3`,
`99_wrapup.mp3`. Put them in `assets/audio/<video-name>/`.

Good lengths: hook 6–12 s, each product 20–45 s, wrap-up 8–15 s.

Paste each paragraph into the scene's `narration:` in the timeline. It becomes the subtitles.
For exact subtitle timing, also save an `.srt` for that voice file and add `subtitles: path/to/file.srt`
to the scene.

## Step 3: Collect clips and photos

For each product, 2–4 short clips (3–8 s each) plus 1 photo is ideal. Name them as in the timeline
(`p03_a.mp4`, `p03_b.mp4`, `p03.jpg`) or change the names in the timeline.

Downloaded Higgsfield clips: `python scripts/sfl.py import-clips "C:\Users\you\Downloads\higgsfield" --to 7-cleaning-gadgets-worth-buying`
copies them in with clean names (your downloads are not touched). Then rename them or put the new
names in the timeline.

If you have fewer clips than voice, clips **repeat** automatically (`fill: cycle`). The QC report
tells you so you can add more footage.

## Step 4: Edit the timeline

Open the `.yaml` file in any text editor (Notepad, TextEdit, or VS Code, which is free and
recommended). Replace every `[text in brackets]`. Rules for YAML files:

- Use **spaces, never tabs**. Indentation matters: keep the same alignment as the template.
- Put text in quotes if it contains `:` or `#`, e.g. `text: "Best for: small kitchens"`.
- Lines starting with `#` are comments and are ignored.

See [TIMELINE-REFERENCE.md](TIMELINE-REFERENCE.md) for every option.

## Step 5: Check

```bash
python scripts/sfl.py check config/timelines/7-cleaning-gadgets-worth-buying.yaml
```

This shows:
- ❌ **errors**, which you must fix (missing files, typos in option names, …). Missing files are listed at the end.
- ⚠️ **warnings**, which are worth reading (placeholder text left, footage repeating, testing claims, music licence not noted).
- the planned length of the video.

## Step 6: Draft, then final

```bash
python scripts/sfl.py build config/timelines/7-cleaning-gadgets-worth-buying.yaml --draft
```
This is quick and lower quality. Watch it and fix the timeline if needed, then make the final:

```bash
python scripts/sfl.py build config/timelines/7-cleaning-gadgets-worth-buying.yaml
```

Output in `output/long-videos/`:
- `<name>.mp4`: the video
- `<name>.srt`: subtitles to upload in YouTube Studio → Subtitles
- `<name>.qc.md`: the quality-control report (open it in VS Code or any Markdown viewer)

Re-renders are faster: prepared clips are cached in `temp/segment-cache/`.

## Step 7: Shorts and thumbnail

See [SHORTS-GUIDE.md](SHORTS-GUIDE.md). For the thumbnail:

```bash
python scripts/sfl.py frames output/long-videos/<name>.mp4 --count 8
```
```bash
python scripts/sfl.py thumbnail --text "7 Cleaning Gadgets Worth Buying" --sub "Researched & compared" --badge "TOP 7" --image thumbnails/frames/<name>/frame_03_....jpg
```

## Step 8: Before uploading
Read the "Before you upload" list at the bottom of the QC report, and [CONTENT-RULES.md](CONTENT-RULES.md).

---

## Changing the look of ALL videos

Edit `config/brand.yaml`: colours, fonts, text sizes, subtitle style, music volume, transition type,
intro and outro text, colour adjustment, watermark or logo. Every video built afterwards uses the new
style.

To change the style of **one** video only, add a `style:` section to its timeline:

```yaml
style:
  colors:
    primary: "#FF6B35"
  audio:
    music_volume_db: -22
```
