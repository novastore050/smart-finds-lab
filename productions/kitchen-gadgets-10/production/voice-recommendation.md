# Voice recommendation — Smart Finds Lab

**Recommendation: Aabo** (`KeU8nqWFDbaoi0QVUjD3`), American English, male, young — as already set in
`config/voice.yaml` (`status: candidate`). Final choice is yours after listening; nothing has been generated.

## Candidates (free ElevenLabs library previews, `productions/_voice-samples/`)

| Voice | Library description | Median pitch* | Pitch variation* | Fit for this channel |
|---|---|---|---|---|
| **Aabo** | Confident explainer; library text names YouTube videos and **product reviews**, clear with numbers | ~114 Hz (low male) | ±35 Hz (steady) | ✅ Best match: built for explainers/product reviews; steady delivery suits a long countdown |
| Quentin | Deep, calm narrator/educator, middle-aged | ~116 Hz (low male) | ±45 Hz (more expressive) | Good alternative if you want warmer, slower, documentary feel |
| Abby | Young, warm, clear female narrator | ~193 Hz | ±40 Hz | Good alternative for a brighter, lifestyle feel |

\*Measured from the preview MP3s with a simple pitch tracker (objective numbers only). Each preview reads different
demo text, so pace and wording cannot be compared fairly — **listen before deciding**.

Why Aabo: the library description is the only one aimed at product reviews/YouTube, his delivery measured the most
stable (helps over ~9 minutes), and you named him as your preferred candidate.

## Settings (keep identical for every video)

| Setting | Value | Why |
|---|---|---|
| model_id | `eleven_multilingual_v2` | Stable, natural long-form narration |
| stability | 0.5 | Natural variation without drifting |
| similarity_boost | 0.75 | Stays close to the original voice |
| style | 0.0 | Avoids exaggerated delivery (and adds no latency) |
| use_speaker_boost | true | Clearer voice |
| speed | 1.0 | Script is timed at ~155 words/min |
| output_format | `mp3_44100_128` | Standard quality for YouTube |

## Before generating (costs credits — ask first)
1. Listen to the three previews; set `voice:` and `status: chosen` in `config/voice.yaml`.
2. Optional cheap test: generate only `s01` (209 characters) and listen.
3. Then the full pack (~7,544 characters per take). The connector makes 2 takes per call by default — ask for 1 to halve the cost.
