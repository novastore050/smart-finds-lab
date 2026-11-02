# Quality-control report — System Test - Master Voice-over

**Status: PASS**  
Created: 2026-11-02 21:21  
Timeline: `config/timelines/test-master-voiceover.yaml`  
Output: `output/long-videos/test-master-voiceover.mp4`  
Format: long (1920x1080, 30 fps)  
Length: 0:28.50  
Render time: 37 s  

Errors: 0 · Warnings: 0 · Passed: 13

## Checks

| | Area | Result |
|---|---|---|
| ℹ️ | Aspect ratio | samples/test-media/image_1_square.jpg is 2000x2000 - it will be reframed to 1920x1080 (fit: auto) |
| ℹ️ | Aspect ratio | samples/test-media/image_2_cutout.png is 1200x1200 - it will be reframed to 1920x1080 (fit: contain) |
| ℹ️ | Aspect ratio | samples/test-media/clip_c_vertical.mp4 is 1080x1920 - it will be reframed to 1920x1080 (fit: auto) |
| ℹ️ | Duration | planned length 0:28.50 |
| ✅ | Subtitles | 4 subtitles; source: file samples/test-media/voiceover_full_placeholder.srt |
| ✅ | Media files | all 5 clip/image files found and readable |
| ✅ | Resolution | 1920x1080 (expected 1920x1080, 16:9) |
| ✅ | Codec | video h264 yuv420p, audio aac 48000 Hz |
| ✅ | Frame rate | 30 fps |
| ✅ | Duration | final video 0:28.50 (planned 0:28.50) |
| ✅ | Audio sync | audio track 28.50s vs video 28.50s (difference 0 ms) |
| ✅ | Audio sync | 1 voice clip(s) placed inside their scenes |
| ✅ | Black frames | no unexpected black sections found |
| ✅ | Silence | no long silent gaps |
| ✅ | Loudness | -14.02 LUFS (target -14.0), true peak -2.58 dBTP |
| ✅ | Subtitles | SRT for YouTube upload: output/long-videos/test-master-voiceover.srt |
| ✅ | Export | output/long-videos/test-master-voiceover.mp4 (9.0 MB) |

## Scenes

| # | Scene | Starts | Length | Clips used | Voice | Subtitles |
|---|---|---|---|---|---|---|
| 1 | a | 0:00.00 | 5.5s | clip_a_left_object.mp4 | master voice-over | — |
| 2 | b | 0:05.00 | 8.0s | clip_b_with_sound.mp4, image_1_square.jpg | master voice-over | — |
| 3 | c | 0:12.50 | 7.0s | image_2_cutout.png | master voice-over | — |
| 4 | d | 0:19.00 | 5.0s | clip_c_vertical.mp4 | master voice-over | — |
| 5 | outro | 0:23.50 | 5.0s | title card | master voice-over | — |

## Before you upload

- Watch the whole video once at normal speed (automated checks cannot judge content).
- Check product names, claims and any numbers on screen are correct.
- Upload the `.srt` file as captions in YouTube Studio (better than auto-captions).
- Add your affiliate disclosure in the description (e.g. *As an Amazon Associate I earn from qualifying purchases*), and tick 'paid promotion' if a brand paid you.
- Add end-screen elements over the outro in YouTube Studio.
