# Quality-control report — Test Short 3 - slice of master voice-over

**Status: PASS WITH WARNINGS**  
Created: 2026-11-02 21:22  
Timeline: `config/shorts/test-demo-shorts.yaml`  
Output: `output/shorts/test-short-03-master-vo.mp4`  
Format: short (1080x1920, 30 fps)  
Length: 0:14.87  
Render time: 19 s  

Errors: 0 · Warnings: 2 · Passed: 13

## Checks

| | Area | Result |
|---|---|---|
| ⚠️ | Timeline | scene 'c': clips are shorter than the voice, so they repeat. Add more footage to this scene for a more professional result. |
| ⚠️ | Duration | Short is 14.9s - your target range is 20-60s |
| ℹ️ | Aspect ratio | samples/test-media/clip_b_with_sound.mp4 is 1920x1080 - it will be reframed to 1080x1920 (fit: auto) |
| ℹ️ | Aspect ratio | samples/test-media/image_1_square.jpg is 2000x2000 - it will be reframed to 1080x1920 (fit: auto) |
| ℹ️ | Aspect ratio | samples/test-media/image_2_cutout.png is 1200x1200 - it will be reframed to 1080x1920 (fit: contain) |
| ✅ | Subtitles | 2 subtitles; source: sliced from master subtitles |
| ✅ | Media files | all 3 clip/image files found and readable |
| ✅ | Resolution | 1080x1920 (expected 1080x1920, 9:16) |
| ✅ | Codec | video h264 yuv420p, audio aac 48000 Hz |
| ✅ | Frame rate | 30 fps |
| ✅ | Duration | final video 0:14.87 (planned 0:14.87) |
| ✅ | Audio sync | audio track 14.85s vs video 14.87s (difference 19 ms) |
| ✅ | Audio sync | 2 voice clip(s) placed inside their scenes |
| ✅ | Black frames | no unexpected black sections found |
| ✅ | Silence | no long silent gaps |
| ✅ | Loudness | -14.11 LUFS (target -14.0), true peak -1.57 dBTP |
| ✅ | Subtitles | SRT for YouTube upload: output/shorts/test-short-03-master-vo.srt |
| ✅ | Export | output/shorts/test-short-03-master-vo.mp4 (3.3 MB) |

## Scenes

| # | Scene | Starts | Length | Clips used | Voice | Subtitles |
|---|---|---|---|---|---|---|
| 1 | b | 0:00.00 | 7.9s | clip_b_with_sound.mp4, image_1_square.jpg | voiceover_full_placeholder.wav | sliced from master subtitles |
| 2 | c | 0:07.63 | 7.2s | image_2_cutout.png | voiceover_full_placeholder.wav | sliced from master subtitles |

## Before you upload

- Watch the whole video once at normal speed (automated checks cannot judge content).
- Check product names, claims and any numbers on screen are correct.
- Upload the `.srt` file as captions in YouTube Studio (better than auto-captions).
- Add your affiliate disclosure in the description (e.g. *As an Amazon Associate I earn from qualifying purchases*), and tick 'paid promotion' if a brand paid you.
- Shorts: make sure nothing important sits under YouTube's buttons (right side / bottom).
