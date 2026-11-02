# Shorts guide

Shorts are made from a **shorts file** in `config/shorts/`. One file can list many Shorts; each
is exported separately to `output/shorts/`, and if one fails, the others still finish.

```bash
python scripts/sfl.py shorts config/shorts/kitchen-gadgets-10-shorts.yaml
```
```bash
python scripts/sfl.py shorts config/shorts/kitchen-gadgets-10-shorts.yaml --only 2
```
```bash
python scripts/sfl.py check config/shorts/kitchen-gadgets-10-shorts.yaml --shorts
```

## Every Short gets automatically

- 1080×1920 (9:16), 30 fps, H.264/AAC MP4
- **Reframing**: 16:9 footage is converted to vertical (see below)
- **Big captions**: 1–3 words at a time, uppercase, one key word highlighted, small pop animation
- **Hook text** in a white box at the top for the first 3 s
- **Call-to-action** at the end ("Full review on the channel")
- Graphics stay out of YouTube's button area (right side) and title area (bottom)
- Music ducking, loudness −14 LUFS, QC report, `.srt`
- A warning if the Short is outside 20–60 s (an error above 3 minutes)

## Option A: reuse scenes from the long video (recommended)

```yaml
defaults:
  from_timeline: config/timelines/kitchen-gadgets-10.yaml
  audio:
    music: assets/music/background-kitchen.mp3
    music_license: "YouTube Audio Library"
  cta: "Full top 10 on the channel"

shorts:
  - output: kitchen10-short-01
    title: "Garlic press Short"
    hook: "This $15 tool replaces three others"
    use_scenes: [p01]          # one or more scene ids from the long timeline
    keep_overlays: true        # keep badges / lower thirds / callouts (default true)
```

The same clips, voice and subtitles are reused. If the long video uses **one master
voice-over file**, the matching part of the voice and subtitles is cut out automatically.
(Per-scene voice files give cleaner cuts.)

## Option B: a Short with its own scenes

Use this when you record a dedicated Short voice-over (often better: tighter, punchier).

```yaml
shorts:
  - output: kitchen10-short-04
    title: "Silicone lids"
    hook: "Stop buying cling film"
    scenes:
      - id: s1
        voice: assets/audio/shorts/lids.mp3
        narration: These stretch lids fit bowls of almost any size ...
        clips:
          - source: assets/video/kitchen-gadgets-10/p04_a.mp4
          - source: assets/video/kitchen-gadgets-10/p04_b.mp4
            fit: cover
            focus_x: 0.3        # crop around the left third
```

All scene options from [TIMELINE-REFERENCE.md](TIMELINE-REFERENCE.md) work here.

## How 16:9 footage becomes 9:16

| `fit` | Result | When to use |
|---|---|---|
| `auto` (default) | The system looks at movement and detail in the clip and crops around the product. If the action is spread across the whole frame, it shows the whole frame on a blurred background so nothing is cut off. | most clips |
| `cover` + `focus_x` | You choose the crop: `0` left, `0.5` centre, `1` right | when auto picks the wrong spot |
| `blur` | Whole frame, blurred background above and below | wide shots, comparisons |
| `cover` | Centre crop | product is in the centre |

The QC report lists what `auto` decided for each clip (e.g. `cover (focus 0.17, detail kept 89%)`).
**Always watch the Short** and override with `focus_x` if the product is cut off.

Vertical source clips (from Higgsfield in 9:16, or phone footage) need no reframing and look best.

## Settings (config/brand.yaml)

```yaml
shorts:
  hook_duration: 3.0
  cta_text: "Full review on the channel"
  fit: auto
  min_seconds: 20
  max_seconds: 60
subtitles:
  short:
    position_y: 0.68        # caption height (0 = top, 1 = bottom)
    max_words: 3
    uppercase: true
    highlight_color: "#FFB020"
```
