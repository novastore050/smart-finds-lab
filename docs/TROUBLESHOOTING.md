# Troubleshooting

First: **read the last lines on screen**, then the full log in `logs/` (the newest file). Every
command writes one.

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Windows: reinstall Python and tick "Add to PATH", or use `py` instead of `python`. Mac: use `python3`. |
| `'ffmpeg' was not found` | Install FFmpeg (docs/INSTALL.md) and open a **new** terminal. Or set the full path: `set SFL_FFMPEG=C:\ffmpeg\bin\ffmpeg.exe` and `set SFL_FFPROBE=C:\ffmpeg\bin\ffprobe.exe` |
| `ModuleNotFoundError: No module named 'yaml'` (or PIL / numpy) | `python -m pip install -r requirements.txt` |
| `doctor` says a filter is MISSING | Your FFmpeg build is too small. Install a **full** build (Windows: `winget install Gyan.FFmpeg`). |
| `There is a typing mistake in …yaml` | The message shows the line. Usually: a **tab** instead of spaces, wrong indentation, or text containing `:` without quotes. |
| `File not found: assets/…` | Check the spelling, the folder and the extension (`.mp4` vs `.MP4` matters on Mac/Linux). Run `check` to list all missing files. |
| `Cannot read media file (damaged or unsupported)` | Re-download or re-export the file. Test it: `python scripts/sfl.py info <file>` |
| `start 12s is after the end of the clip` | The trim `start:` is longer than the clip. Use `info` to see the clip length. |
| Clips repeat in a scene (warning) | The voice is longer than the clips. Add more clips, or use `fill: slow` / `fill: freeze`. |
| Subtitles are out of sync | Narration-based timing is an estimate. Use an `.srt` for that voice file (`subtitles:` in the scene) or install Whisper (`subtitles: mode: whisper`). Also check that `narration` matches what is actually said. |
| Product is cut off in a Short | Add `fit: cover` and `focus_x: 0.2` (left) … `0.8` (right) to that clip, or `fit: blur` to show the whole frame. |
| Music too loud / quiet | `music_volume_db` in `config/brand.yaml` (all videos) or in the timeline's `audio:` (one video). −22 is quieter, −16 is louder. |
| Text too small / big | `text_sizes` in `config/brand.yaml`. |
| Video renders slowly | Use `--draft` while editing. Final quality: `preset: fast` in brand.yaml `formats` (slightly bigger file). Re-renders reuse prepared clips from `temp/segment-cache/`. |
| "No space left on device" | Delete the `temp/` folder (it's safe) and old drafts in `output/`. |
| A new export is called `name_v2.mp4` | That's intentional: exports are never overwritten. Add `--overwrite` to replace. |
| Strange errors after editing brand.yaml | Compare with the original layout. Missing keys fall back to built-in defaults, but the indentation must be correct. |
| QC: "Loudness" warning | Usually very quiet or very dynamic source audio. Check that the voice files aren't nearly silent. |
| QC: "Black frames" warning | A clip contains black sections. Trim it with `start`/`end`. |
| QC: "Silence" warning | A gap with no voice or music. Check that all voice files are set, or add music. |

## Still stuck?
Keep the log file from `logs/` and the timeline `.yaml`. They contain everything needed to diagnose the problem.
