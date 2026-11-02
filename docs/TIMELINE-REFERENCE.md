# Timeline reference

A timeline is a `.yaml` file (a `.json` file with the same structure also works) in `config/timelines/`.
Only `project.title` and `scenes` are required. Everything else is optional.

## Complete example

```yaml
project:
  title: "10 Kitchen Gadgets That Actually Make Life Easier"   # video title (also saved in the MP4)
  output: kitchen-gadgets-10      # output file name → output/long-videos/kitchen-gadgets-10.mp4
  format: long                    # long (16:9) or short (9:16)
  fps: 30                         # optional, default from brand.yaml

audio:
  music: assets/music/background-kitchen.mp3
  music_license: "YouTube Audio Library - no attribution"   # QC warns if empty
  music_volume_db: -19            # optional: overrides brand.yaml for this video
  music_start: 0                  # optional: start the music N seconds into the track
  duck_music_under_voice: true    # optional
  # One single voice-over file for the whole video (instead of one per scene):
  # voiceover: assets/audio/my-video/full-voiceover.mp3
  # voiceover_start: 2.6          # seconds into the video where it starts

subtitles:
  mode: auto        # auto | srt | script | whisper | none
  burn_in: true     # draw subtitles on the video
  export_srt: true  # also save an .srt for YouTube
  # file: subtitles/my-video.srt  # only with a single master voice-over

intro:                    # overrides brand.yaml intro settings for this video
  enabled: true
  position: after_first_scene   # start | after_first_scene
  title: null             # null = channel name
outro:
  enabled: true
  duration: 12

style: {}                 # optional per-video override of anything in brand.yaml

scenes:
  - id: p03                         # unique name (letters/numbers)
    voice: assets/audio/my-video/03.mp3
    narration: >
      The text spoken in this scene. Used for subtitles when there is no .srt file.
    subtitles: subtitles/my-video-03.srt   # optional exact subtitles for THIS voice file
    transition: fade                # how this scene STARTS (see list below)
    transition_duration: 0.5
    fill: cycle                     # cycle | freeze | slow  (when clips are shorter than the voice)
    clips:
      - source: assets/video/my-video/p03_a.mp4
        start: 2.0                  # trim: skip the first 2 seconds
        end: 7.5                    # trim: stop at 7.5 s
      - source: assets/video/my-video/p03_b.mp4
        speed: 0.8                  # slow motion (0.25 - 4)
        clip_audio: 0.3             # keep 30 % of the clip's own sound (default 0 = muted)
      - source: assets/images/my-video/p03.jpg
        duration: 4                 # seconds on screen
        motion: zoom_in             # none | zoom_in | zoom_out | pan_left | pan_right | pan_up | pan_down
        fit: contain                # cover | contain | blur
    overlays:
      - type: badge
        text: "#3"
      - type: lower_third
        text: "Product name"
        subtitle: "Best for: small kitchens"
        start: 0.8                  # seconds after the scene starts
        duration: 4.5
      - type: callout
        text: "Dishwasher safe"
        start: 6
    sfx:
      - file: assets/sound-effects/generated/ding.wav
        at: 6.0                     # seconds after the scene starts
        volume_db: -3
    look:                           # optional colour override for this scene
      brightness: 0.03
    shorts:                         # optional settings used when this scene is reused in a Short
      fit: cover
      focus_x: 0.3
```

## Scene length: how it's decided

1. If the scene has `duration:`, that is its length.
2. Otherwise, if it has a `voice:`, the length is the transition + 0.15 s + voice length + 0.45 s pause.
3. Otherwise, it is the total length of its clips.

If clips are **shorter** than the scene: `fill: cycle` (default) repeats the clips in order,
`freeze` holds the last frame, and `slow` slows all clips evenly (up to 1.6×).
If clips are **longer**, they are cut at the end of the scene.

## Scene shortcuts

A scene with only one clip can skip `clips:`:

```yaml
  - id: b-roll
    source: assets/video/my-video/kitchen.mp4
    start: 3
    duration: 5
```

A **title card** (text on a branded background):

```yaml
  - id: chapter-2
    type: card
    title: "Best Under $20"
    subtitle: "Budget picks"
    background: gradient        # gradient | "#123A4A" | path/to/image.jpg (blurred)
    duration: 3
```

## Clip options

| Option | Meaning | Default |
|---|---|---|
| `source` | video (`.mp4 .mov .mkv .webm`) or image (`.jpg .png .webp`) | required |
| `start` / `end` | trim in / out point in seconds (video) | whole clip |
| `duration` | how long it stays on screen | image: 4 s, video: its trimmed length |
| `fit` | `cover` fills the frame and crops the edges. `contain` shows the whole picture on a clean background. `blur` shows the whole picture on a blurred copy. `auto` picks for you. | `auto` |
| `focus_x` / `focus_y` | where to crop when using `cover` (0 = left/top, 0.5 = centre, 1 = right/bottom) | centre / auto |
| `motion` | photo movement (Ken Burns) | `zoom_in` |
| `speed` | 0.5 = half speed, 2 = double speed | 1 |
| `clip_audio` | volume of the clip's own sound, 0–1 | 0 |
| `background` | colour behind transparent PNG / `contain` photos | `#F2F4F7` |

**Vertical clips in a 16:9 video** are shown whole on a blurred background automatically.

## Overlay types

| type | Looks like | Main options |
|---|---|---|
| `title` | Big centred title, pops in, accent line | `text`, `subtitle`, `position`, `size` |
| `badge` | Rounded square with number, e.g. `#3` (top-left, stays for the whole scene) | `text`, `position` |
| `lower_third` | Product name box that wipes in from the left | `text`, `subtitle`, `position` |
| `callout` | Coloured pill that slides in ("Dishwasher safe") | `text`, `position`, `color`, `text_color` |
| `cta` | Teal pill with ↓ arrow ("Links in the description") | `text`, `position`, `arrow: false` |
| `text` | Free text | `text`, `position`, `size`, `font` (heading/body/caption), `color`, `box: true` |
| `hook` | Big boxed text at the top (made for Shorts) | `text`, `uppercase` |

All overlays accept `start` (seconds after the scene starts) and `duration` (seconds, or `scene`
to stay until the scene ends). `badge` lasts the whole scene by default.
Badges and titles play a "pop" sound (set `sfx: false` to turn it off).

**position** can be one of: `top-left`, `top`, `top-right`, `left`, `center`, `right`,
`bottom-left`, `bottom`, `bottom-right`, or exact pixels: `position: {x: 200, y: 150}`.

## Transitions

`cut` (no transition), `fade`, `fadeblack`, `fadewhite`, `dissolve`, `wipeleft`, `wiperight`, `wipeup`,
`wipedown`, `slideleft`, `slideright`, `slideup`, `slidedown`, `smoothleft`, `smoothright`, `smoothup`,
`smoothdown`, `circleopen`, `circleclose`, `radial`, `distance`, `pixelize`, `zoomin`, `hblur`.

For a clean, professional look, use `fade` for most scenes (the default) and `cut` within fast
sequences. Transitions play a soft whoosh (`audio.transition_sfx` in brand.yaml; set it to `null` to turn it off).

## Subtitle modes

| mode | Where the subtitles come from |
|---|---|
| `auto` | for each scene: its `.srt` file if given → Whisper (if installed and no narration) → narration text |
| `srt` | only from `.srt` files (exact timing) |
| `script` | only from narration text (timing **estimated** from text length) |
| `whisper` | transcribe the voice files with faster-whisper (exact timing, optional install) |
| `none` | no subtitles |

`.srt` timings are relative to **the start of the voice file they belong to**, which is how
voice-over tools export them.

## Extending the system

The code is in `scripts/sfl_engine/`:

| File | Responsibility |
|---|---|
| `config.py` | reads YAML, default brand settings |
| `plan.py` | calculates timing (frame-accurate) |
| `render.py` | prepares each clip (trim, reframe, colour, Ken Burns) |
| `reframe.py` | automatic 16:9 → 9:16 reframing |
| `graphics.py` | titles, badges, lower thirds, subtitles (ASS format) |
| `audio.py` | voice, music ducking, SFX, loudness |
| `builder.py` | joins everything, exports MP4, Shorts |
| `qc.py` | quality checks and reports |
| `tools.py` | sound effects, test media, import, thumbnails, new project |

To add a new overlay style, add a method to `Graphics` in `graphics.py` with the same name as the
new `type`, and add the name to `OVERLAY_TYPES` in `config.py`.
