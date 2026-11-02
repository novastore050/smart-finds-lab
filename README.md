# Smart Finds Lab: Automated Video Production

**Discover. Compare. Buy Smarter.**

This folder turns your clips, product photos, voice-overs and music into finished YouTube videos:

- **Long-form videos** at 1920×1080 (16:9), H.264 + AAC MP4, 30 fps
- **YouTube Shorts** at 1080×1920 (9:16), with automatic reframing and big captions
- **Subtitles** burned into the video, plus an `.srt` file to upload to YouTube
- **Motion graphics**: title, number badges (#1…#10), lower thirds, callouts, call-to-action, intro sting, end screen
- **Audio**: voice clean-up, background music that ducks under the voice, sound effects, YouTube loudness (−14 LUFS)
- **Quality-control report** for every video

You describe a video in a simple text file (a **timeline**). The system does the editing with
**FFmpeg**, so you don't need to edit in CapCut.

---

## Quick start (5 commands)

Open a terminal **inside the `Smart-Finds-Lab` folder**, then:

```bash
python scripts/sfl.py doctor
```
Checks that FFmpeg and Python are installed. If something is missing, see [docs/INSTALL.md](docs/INSTALL.md).

```bash
python scripts/sfl.py make-sfx
```
Creates free sound effects (whoosh, pop, ding, …). You only need to run this once.

```bash
python scripts/sfl.py check config/timelines/kitchen-gadgets-10.yaml
```
Lists every file the video still needs and any problems. Nothing is rendered.

```bash
python scripts/sfl.py build config/timelines/kitchen-gadgets-10.yaml
```
Makes the long video. The result goes to `output/long-videos/`.

```bash
python scripts/sfl.py shorts config/shorts/kitchen-gadgets-10-shorts.yaml
```
Makes the Shorts. The results go to `output/shorts/`.

> On some computers the command is `python3` instead of `python`, and on Windows it may be `py`.

### Try it without your own media

```bash
python scripts/sfl.py make-test-media
```
```bash
python scripts/sfl.py build config/timelines/test-demo.yaml
```
```bash
python scripts/sfl.py shorts config/shorts/test-demo-shorts.yaml
```
This creates clearly labelled placeholder clips (no real products) and renders test videos,
so you can see every feature working. Never publish these test videos.

---

## Folder map

| Folder | What goes there |
|---|---|
| `assets/video/` | Your video clips (Higgsfield, stock you have rights to, your own footage). Use one sub-folder per video, e.g. `assets/video/kitchen-gadgets-10/` |
| `assets/images/` | Product photos (JPG/PNG; transparent PNG cut-outs are fine) |
| `assets/audio/` | Voice-over recordings (MP3/WAV/M4A), one sub-folder per video |
| `assets/music/` | Background music **you have the rights to** |
| `assets/sound-effects/` | Sound effects (`generated/` is made by `make-sfx`) |
| `assets/fonts/` | Brand fonts (Inter, free licence, already included) |
| `config/brand.yaml` | **Your channel style**: colours, fonts, sizes, music level, intro and outro |
| `config/timelines/` | One timeline file per long video |
| `config/shorts/` | One file listing the Shorts for a video |
| `subtitles/` | Your `.srt` subtitle files (optional) |
| `thumbnails/` | Thumbnails made with the `thumbnail` command |
| `output/long-videos/` | Finished long videos + `.srt` + QC report |
| `output/shorts/` | Finished Shorts + `.srt` + QC report |
| `temp/` | Working files. Safe to delete at any time (it makes the next render slower). |
| `logs/` | Detailed logs of every run (useful when something fails) |
| `docs/` | Guides |
| `scripts/` | The program (you don't need to edit it) |
| `samples/` | Generated test media (placeholders only) |

**Safety:** the system only **reads** your media. It never changes, moves or deletes files in
`assets/`. Finished videos are never overwritten: a second export becomes `name_v2.mp4`
(unless you add `--overwrite`).

---

## All commands

| Command | What it does |
|---|---|
| `python scripts/sfl.py doctor` | Checks installed software, fonts and disk space |
| `python scripts/sfl.py check <timeline>` | Pre-flight check: lists missing files and problems, writes a `.precheck.md` report |
| `python scripts/sfl.py check <shorts-file> --shorts` | Same check, for a Shorts file |
| `python scripts/sfl.py build <timeline>` | Renders a long-form video |
| `python scripts/sfl.py build <timeline> --draft` | Fast, lower-quality preview (`_draft.mp4`) |
| `python scripts/sfl.py shorts <shorts-file>` | Renders all Shorts in the file |
| `python scripts/sfl.py shorts <shorts-file> --only 2` | Renders only Short number 2 (or use its name) |
| `python scripts/sfl.py new "Video Title" --products 7` | Creates a new timeline and media folders from the template |
| `python scripts/sfl.py import-clips <folder> --to <video-name>` | **Copies** downloaded clips (e.g. from Higgsfield) into `assets/video/<video-name>/`, with a manifest |
| `python scripts/sfl.py thumbnail --text "..." --image <photo>` | Makes a 1280×720 thumbnail |
| `python scripts/sfl.py frames <video> --count 8` | Saves still frames you can use for a thumbnail |
| `python scripts/sfl.py make-sfx` | Generates copyright-free sound effects |
| `python scripts/sfl.py make-test-media` | Generates labelled placeholder media for testing |
| `python scripts/sfl.py info <file>` | Shows the resolution, length, etc. of a media file |

---

## Guides

1. [docs/INSTALL.md](docs/INSTALL.md): install Python + FFmpeg (Windows / Mac)
2. [docs/EDITING-GUIDE.md](docs/EDITING-GUIDE.md): step-by-step workflow for a new video
3. [docs/TIMELINE-REFERENCE.md](docs/TIMELINE-REFERENCE.md): every option you can write in a timeline
4. [docs/SHORTS-GUIDE.md](docs/SHORTS-GUIDE.md): making Shorts
5. [docs/FIRST-VIDEO-CHECKLIST.md](docs/FIRST-VIDEO-CHECKLIST.md): **the exact files needed for "10 Kitchen Gadgets"**
6. [docs/HIGGSFIELD.md](docs/HIGGSFIELD.md): using Higgsfield AI clips
7. [docs/CONTENT-RULES.md](docs/CONTENT-RULES.md): honesty, copyright, Amazon affiliate rules
8. [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md): fixes for common problems
