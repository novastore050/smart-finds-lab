# Quality-control report — Test Short 2 - custom scenes

**Status: PASS**  
Created: 2026-11-02 21:22  
Timeline: `config/shorts/test-demo-shorts.yaml`  
Output: `output/shorts/test-short-02-custom.mp4`  
Format: short (1080x1920, 30 fps)  
Length: 0:22.30  
Render time: 35 s  

Errors: 0 · Warnings: 0 · Passed: 13

## Checks

| | Area | Result |
|---|---|---|
| ℹ️ | Aspect ratio | samples/test-media/clip_a_left_object.mp4 is 1920x1080 - it will be reframed to 1080x1920 (fit: auto) |
| ℹ️ | Aspect ratio | samples/test-media/clip_b_with_sound.mp4 is 1920x1080 - it will be reframed to 1080x1920 (fit: auto) |
| ℹ️ | Aspect ratio | samples/test-media/image_1_square.jpg is 2000x2000 - it will be reframed to 1080x1920 (fit: auto) |
| ℹ️ | Subtitles | 5 subtitles; source: script text (estimated timing) - timing is estimated from the script; check it, or use an .srt / Whisper for exact sync |
| ✅ | Duration | Short length 22.3s is inside 20-60s |
| ✅ | Media files | all 3 clip/image files found and readable |
| ✅ | Resolution | 1080x1920 (expected 1080x1920, 9:16) |
| ✅ | Codec | video h264 yuv420p, audio aac 48000 Hz |
| ✅ | Frame rate | 30 fps |
| ✅ | Duration | final video 0:22.30 (planned 0:22.30) |
| ✅ | Audio sync | audio track 22.30s vs video 22.30s (difference 0 ms) |
| ✅ | Audio sync | 3 voice clip(s) placed inside their scenes |
| ✅ | Black frames | no unexpected black sections found |
| ✅ | Silence | no long silent gaps |
| ✅ | Loudness | -14.02 LUFS (target -14.0), true peak -2.27 dBTP |
| ✅ | Subtitles | SRT for YouTube upload: output/shorts/test-short-02-custom.srt |
| ✅ | Export | output/shorts/test-short-02-custom.mp4 (5.3 MB) |

## Scenes

| # | Scene | Starts | Length | Clips used | Voice | Subtitles |
|---|---|---|---|---|---|---|
| 1 | s1 | 0:00.00 | 7.6s | clip_a_left_object.mp4 *(auto: cover (focus 0.17, detail kept 74%))* | voice_03_placeholder.wav | script text (estimated timing) |
| 2 | s2 | 0:07.30 | 8.9s | clip_b_with_sound.mp4, image_1_square.jpg *(auto: blur (focus 0.50, detail kept 43%))* | voice_02_placeholder.wav | script text (estimated timing) |
| 3 | s3 | 0:15.90 | 6.4s | clip_a_left_object.mp4 | voice_01_placeholder.wav | script text (estimated timing) |

## Before you upload

- Watch the whole video once at normal speed (automated checks cannot judge content).
- Check product names, claims and any numbers on screen are correct.
- Upload the `.srt` file as captions in YouTube Studio (better than auto-captions).
- Add your affiliate disclosure in the description (e.g. *As an Amazon Associate I earn from qualifying purchases*), and tick 'paid promotion' if a brand paid you.
- Shorts: make sure nothing important sits under YouTube's buttons (right side / bottom).
