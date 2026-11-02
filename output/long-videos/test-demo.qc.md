# Quality-control report — System Test - Placeholder Media

**Status: PASS WITH WARNINGS**  
Created: 2026-11-02 21:20  
Timeline: `config/timelines/test-demo.yaml`  
Output: `output/long-videos/test-demo.mp4`  
Format: long (1920x1080, 30 fps)  
Length: 0:37.20  
Render time: 57 s  

Errors: 0 · Warnings: 4 · Passed: 12

## Checks

| | Area | Result |
|---|---|---|
| ⚠️ | Subtitles | 2 subtitle(s) need fast reading (> 22 characters/second) |
| ⚠️ | Timeline | scene 'p02': clips are shorter than the voice, so they repeat. Add more footage to this scene for a more professional result. |
| ⚠️ | Timeline | scene 'p01': clips are shorter than the voice, so they repeat. Add more footage to this scene for a more professional result. |
| ⚠️ | Timeline | scene 'wrapup': clips are shorter than the voice, so they repeat. Add more footage to this scene for a more professional result. |
| ℹ️ | Aspect ratio | samples/test-media/image_1_square.jpg is 2000x2000 - it will be reframed to 1920x1080 (fit: auto) |
| ℹ️ | Aspect ratio | samples/test-media/clip_c_vertical.mp4 is 1080x1920 - it will be reframed to 1920x1080 (fit: auto) |
| ℹ️ | Aspect ratio | samples/test-media/image_2_cutout.png is 1200x1200 - it will be reframed to 1920x1080 (fit: contain) |
| ℹ️ | Subtitles | 10 subtitles; source: file samples/test-media/voice_02_placeholder.srt, script text (estimated timing) - timing is estimated from the script; check it, or use an .srt / Whisper for exact sync |
| ℹ️ | Duration | planned length 0:37.20 |
| ✅ | Media files | all 6 clip/image files found and readable |
| ✅ | Resolution | 1920x1080 (expected 1920x1080, 16:9) |
| ✅ | Codec | video h264 yuv420p, audio aac 48000 Hz |
| ✅ | Frame rate | 30 fps |
| ✅ | Duration | final video 0:37.20 (planned 0:37.20) |
| ✅ | Audio sync | audio track 37.20s vs video 37.20s (difference 0 ms) |
| ✅ | Audio sync | 4 voice clip(s) placed inside their scenes |
| ✅ | Black frames | no unexpected black sections found |
| ✅ | Silence | no long silent gaps |
| ✅ | Loudness | -14.02 LUFS (target -14.0), true peak -2.31 dBTP |
| ✅ | Subtitles | SRT for YouTube upload: output/long-videos/test-demo.srt |
| ✅ | Export | output/long-videos/test-demo.mp4 (9.2 MB) |

## Scenes

| # | Scene | Starts | Length | Clips used | Voice | Subtitles |
|---|---|---|---|---|---|---|
| 1 | hook | 0:00.00 | 6.1s | clip_a_left_object.mp4, image_1_square.jpg | voice_01_placeholder.wav | script text (estimated timing) |
| 2 | intro | 0:05.63 | 2.6s | title card | — | — |
| 3 | p02 | 0:07.73 | 9.2s | clip_b_with_sound.mp4, clip_c_vertical.mp4 | voice_02_placeholder.wav | file samples/test-media/voice_02_placeholder.srt |
| 4 | p01 | 0:16.40 | 8.2s | clip_d_very_short.mp4, image_2_cutout.png | voice_03_placeholder.wav | script text (estimated timing) |
| 5 | chapter | 0:24.07 | 2.5s | title card | — | — |
| 6 | wrapup | 0:26.07 | 5.6s | clip_a_left_object.mp4 | voice_04_placeholder.wav | script text (estimated timing) |
| 7 | outro | 0:31.20 | 6.0s | title card | — | — |

## Before you upload

- Watch the whole video once at normal speed (automated checks cannot judge content).
- Check product names, claims and any numbers on screen are correct.
- Upload the `.srt` file as captions in YouTube Studio (better than auto-captions).
- Add your affiliate disclosure in the description (e.g. *As an Amazon Associate I earn from qualifying purchases*), and tick 'paid promotion' if a brand paid you.
- Add end-screen elements over the outro in YouTube Studio.
