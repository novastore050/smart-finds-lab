# First video: "10 Kitchen Gadgets That Actually Make Life Easier"

Timeline: `config/timelines/kitchen-gadgets-10.yaml` · Shorts: `config/shorts/kitchen-gadgets-10-shorts.yaml`

The system is ready. These are the **47 files you need to provide**. You can always get the
current list with:

```bash
python scripts/sfl.py check config/timelines/kitchen-gadgets-10.yaml
```

The empty folders already exist.

## 1. Voice-over: `assets/audio/kitchen-gadgets-10/` (12 files)

| File | Content | Suggested length |
|---|---|---|
| `00_hook.mp3` | Hook | 6–12 s |
| `10.mp3`, `09.mp3`, … `01.mp3` | One per product (#10 counts down to #1) | 20–45 s each |
| `99_wrapup.mp3` | Summary + "links in the description" + question for comments | 8–15 s |

MP3, WAV or M4A all work. Paste each script paragraph into the matching `narration:` in the
timeline (it becomes the subtitles). With 10 × ~30 s, the video is about 6–7 minutes.

## 2. Video clips: `assets/video/kitchen-gadgets-10/` (24 files)

| File | Content |
|---|---|
| `hook_a.mp4`, `hook_b.mp4`, `hook_c.mp4` | 3 fast, attractive clips (best moments of your top products) |
| `p10_a.mp4`, `p10_b.mp4` … `p01_a.mp4`, `p01_b.mp4` | 2 clips per product, 3–8 s each, showing the product **in use** |
| `wrapup.mp4` | A calm kitchen / overview clip |

16:9 or 9:16 clips both work (9:16 clips are shown on a blurred background in the long video and
fit Shorts perfectly). Use 1080p or better. Only use footage you have the right to use (see
[CONTENT-RULES.md](CONTENT-RULES.md)). More clips per product = a more professional result: just add
lines under `clips:`.

## 3. Product photos: `assets/images/kitchen-gadgets-10/` (10 files)

`p10.jpg` … `p01.jpg`: one clear photo per product, at least 1500 px. A transparent PNG cut-out
also works (write `p01.png` in the timeline and add `fit: contain`).

## 4. Music: `assets/music/` (1 file)

`background-kitchen.mp3`: calm, upbeat instrumental, **with a licence that allows YouTube use**
(e.g. YouTube Studio → Audio Library). Write its source in `music_license:` in the timeline.

## 5. Text to fill in the timeline

Replace every `[…]` in `config/timelines/kitchen-gadgets-10.yaml`:

- the hook and narration for each scene
- for each product: `[Product N name]`, `[Best for: …]`, `[Key feature]`
- `music_license`

And in `config/shorts/kitchen-gadgets-10-shorts.yaml`: the hook line for each Short.

`check` warns about every bracket left, and about wording that claims hands-on testing.

## 6. Then

```bash
python scripts/sfl.py check config/timelines/kitchen-gadgets-10.yaml
```
```bash
python scripts/sfl.py build config/timelines/kitchen-gadgets-10.yaml --draft
```
```bash
python scripts/sfl.py build config/timelines/kitchen-gadgets-10.yaml
```
```bash
python scripts/sfl.py shorts config/shorts/kitchen-gadgets-10-shorts.yaml
```

### Don't have everything yet?
Delete lines you don't need (e.g. a `- source:` line for a missing photo). A scene needs at least
one clip or photo. With only a voice file and one photo, the photo slowly zooms for the whole voice.
That works but looks static, so add clips when you can.
