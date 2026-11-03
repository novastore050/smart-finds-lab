# ElevenLabs voice-over (stage 7)

One voice for the whole channel: `config/voice.yaml` (voice_id, model, settings, pronunciations).
Initial choice: **Aabo** (`KeU8nqWFDbaoi0QVUjD3`), compared with Quentin and Abby
(`studio.py voice-samples` downloads their FREE public previews to `productions/_voice-samples/`).
Never change voice/model/settings between videos unless the owner decides to rebrand.

## Step 1 — export (free)

`studio.py voice-pack <slug>` writes `voice/text/<scene>.txt` (pronunciation fixes applied),
`voice/voice-jobs.json` (voice, model, settings, characters per scene) and `voice/README.md`.

## Step 2 — cost check and approval (free, then STOP)

With the ElevenLabs connector: call `creative_generate_speech` with `estimate_only: true` for the jobs
(same `voice_id`, `model_id`) and tell the owner the credit cost. **Do not generate until the owner says yes.**

## Step 3 — generate (only after approval)

Option B (connector, in session): for each job call `creative_generate_speech(prompt=<text>,
voice_id=<voice_id>, model_id=<model_id>)` on one flow (`creative_create_flow` first), poll
`creative_get_flow_run_status`, then `creative_get_generations` for the `full_res_url`.
- Try to download the file into `productions/<slug>/voice/<scene>.mp3` (curl). If the host is blocked in
  the cloud session, give the owner the flow URL and ask them to download the takes, named by scene.
- Never call generate twice to "retry" — each call charges.
- Each call may produce 2 takes by default; mention that this doubles the cost, or ask the owner.

Option A (manual): owner uses the ElevenLabs website with the same voice + settings.
Option C (API, owner's computer): `ELEVENLABS_API_KEY=... python scripts/studio.py tts <slug> --confirm-spend`
(dry run without the flag). Not live-tested from the build environment.

## Step 4 — import + exact subtitles

`studio.py import-voice <slug> <folder>` copies files whose names contain the scene id (`s01`, `s02`…)
plus any `*.json` timing / `.srt` files, and warns if a file's length doesn't match the script.

Word-level timing (exact subtitles), any of:
- connector: upload the audio to the flow and run `creative_transcribe_audio` (costs a little — ask first);
  save the returned `words` (start/end per word) as `voice/<scene>.words.json`;
- API option C saves `alignment` automatically;
- Whisper (free, local, optional install) is used by the editor if installed.
Then `studio.py align <slug>` → `voice/<scene>.srt`, which `build-timeline` uses automatically.
Without timings, subtitles fall back to estimated timing from the script (QC warns).
