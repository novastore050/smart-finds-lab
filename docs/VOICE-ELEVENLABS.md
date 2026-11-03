# Voice-over with ElevenLabs

## One voice for the whole channel

`config/voice.yaml` stores the channel voice. Every video uses the same voice, model and settings, so
Smart Finds Lab always sounds the same.

- **Current choice:** **Aabo**, an American male voice that the ElevenLabs library describes for
  "YouTube videos, product reviews" (`status: candidate`).
- **Compared with:** Quentin (deeper, calmer, middle-aged American male) and Abby (young American female).

Download the free public previews (no credits used) and listen:

```bash
python scripts/studio.py voice-samples
```

The files go to `productions/_voice-samples/`. When you've decided, set `status: chosen` (and change
`voice:` if you pick someone else).

**Pronunciation:** add brand names the voice gets wrong under `pronunciations:`, e.g. `OXO: "ox-oh"`. Only
the voice text changes; subtitles keep the real spelling.

## Cost

ElevenLabs charges per character. `python scripts/studio.py voice-pack <video>` shows the total. A
6–7 minute video is about 6,000–7,000 characters, roughly 6,000–7,000 credits on standard models, or
about half on Flash/Turbo models. Check your ElevenLabs plan for what that costs. **Nothing is generated
without your OK.**

## Three ways to generate

**A) ElevenLabs website (manual, simplest)**
1. Open Text to Speech and choose the same voice.
2. Set the same model and settings (shown in `voice/README.md`).
3. Paste each `voice/text/sXX.txt`.
4. Download each as MP3 named `s01.mp3`, `s02.mp3`, and so on.
5. Import them:

```bash
python scripts/studio.py import-voice <video> <folder>
```

**B) Ask Claude (ElevenLabs connector)**
Claude reads `voice/voice-jobs.json`, shows you the credit estimate, and only generates after you say
yes. If Claude can't download the files in a cloud session, it gives you the link to download them;
then use `import-voice`.

**C) API on your own computer** (optional, for full automation)
1. Create an API key in your ElevenLabs account.
2. Store it as an environment variable. **Never put it in a file in this project.**
   - Windows: `setx ELEVENLABS_API_KEY "your-key"`, then open a new terminal.
   - Mac/Linux: `export ELEVENLABS_API_KEY=your-key`
3. Run it as a dry run first (no credits are used):

```bash
python scripts/studio.py tts <video>
```

4. Then generate for real:

```bash
python scripts/studio.py tts <video> --confirm-spend
```

This saves the audio, the word timings and exact subtitles. *This path was built to ElevenLabs'
documented text-to-speech-with-timestamps endpoint, but it could not be tested live from the build
environment (no key, API blocked, and it costs credits). Try it on one scene first:
`--scene s01 --confirm-spend`.*

## Exact subtitles

Subtitles match the voice exactly when word timings exist:
- **API (C):** timings are saved automatically.
- **Connector (B):** Claude can transcribe the audio with word timestamps. This costs a small amount, so
  you'll be asked first.
- **Whisper:** free and offline. Install it with `pip install faster-whisper` (about 500 MB download, ask
  before installing).

Convert the timings into subtitle files:

```bash
python scripts/studio.py align <video>
```

Without timings, subtitles are spread over the voice using the script text. They are close but not
exact, and the QC report warns you.
