# Voice test preparation — Aabo (2026-11-03)

**Prepared only.** No audio was generated, no paid API was called, no credits were spent, nothing was bought. The
only ElevenLabs calls were free: a voice search and two `estimate_only` price checks. Note: each price check
created an empty "flow" page in the ElevenLabs workspace; nothing was generated or charged.

Aabo (`KeU8nqWFDbaoi0QVUjD3`, "Engaging Confident Explainer Voice", American male) is available in the connected
workspace. Its description mentions YouTube narration and "numbers and long-form scripts".

## 1. Best test segment (≈26 s)

Source: long video, scene **s11 (#2 TP19H)**, first five sentences. 67 words, ~26 s at 155 wpm, 407 characters
as sent to the voice.

> Number two. Cutting into chicken to check it can let some of the juices escape, and guessing can leave it
> overcooked or undercooked. The TP19H instant-read thermometer, sold under the TempPro name, formerly ThermoPro,
> fixes that. Flip out the probe, and according to its manual, the backlit screen shows a reading in about three
> to four seconds. It's water resistant and has a magnet on the back.

Why this one (chosen by scanning every 20–30 s window in the 13 scenes and 3 Shorts):
- It has the most risky names in one natural passage: TP19H, TempPro, ThermoPro.
- It has numbers ("three to four seconds") and a sourced phrase ("according to its manual").
- It tests the countdown opener ("Number two."), a problem → solution turn, and a list-style sentence.
- It's the delivery style of most of the video: calm explainer, not hype.

Zulay and Microplane don't appear in any 20–30 s window together with TP19H, so they're tested in a separate
pronunciation file (§2).

Files: `test-passage-voice.txt` (exact text for the voice, with pronunciation fixes) and
`test-passage-subtitles.txt` (normal spelling).

## 2. Pronunciation: three versions to compare

`pronunciation-lines.txt` has one line per version (~10 s each) plus one line with the other brand names.

| Name | Version A | Version B | Version C | Notes |
|---|---|---|---|---|
| **Zulay** | **"Soo-lay"** | "Zoo-lay" (current setting) | "Zuh-lay" | Zulay Kitchen is named after the founder's mother, raised in Venezuela. Name sites give the personal name as roughly "soo-LAY" (Spanish). **The brand's own spoken pronunciation was not found.** A suggests origin, B is how most US viewers will read it. Best check: a Zulay Kitchen video or ask the brand. |
| **TP19H** | **"T P nineteen H"** (current setting) | "T P one nine H" | "T P nineteen aitch" | A is how model numbers are usually read in reviews; C only if the voice says "H" oddly. |
| **Microplane** | "Microplane" (no change) | **"Micro-plane"** (current setting) | "My-kro-plane" | Standard is MY-kroh-playn. A shows whether the voice already gets it right without help. |

Other names in the extra line: OXO → "ox-oh", PowerLix → "Power Licks", TempPro → "Temp Pro", ThermoPro →
"Thermo Pro", plus Fullstar, Rubbermaid Brilliance and KitchenAid unchanged (as a check).

How the fix is applied: our pipeline already swaps the spelling **only in the text sent to the voice**
(`config/voice.yaml → pronunciations`); subtitles keep the real spelling. That works with every model. For use on
the ElevenLabs website, `pronunciation-dictionary.pls` has the same rules as **alias** rules. ElevenLabs' docs say
`eleven_multilingual_v2` does **not** support IPA/phoneme rules, only alias rules
([ElevenLabs pronunciation docs](https://elevenlabs.io/docs/best-practices/prompting/pronunciation),
[dictionaries](https://elevenlabs.io/docs/conversational-ai/customization/voice/pronunciation-dictionary)).

## 3. Free options and their limits

| Option | Cost | Hears our script? | Limits |
|---|---|---|---|
| Voice-library preview of Aabo | Free | No (generic sample sentence) | Already downloaded earlier; only judges the general sound |
| `estimate_only` price check (connector) | Free | No audio | Price only (used for this report) |
| **ElevenLabs Free account** on elevenlabs.io | Free | **Yes** | About **10,000 credits/month** (the test needs 1,018); **no commercial licence**, and free-plan output used publicly must credit elevenlabs.io. Fine for a private test; **not** for the published video. |
| Generate through the connector here | Uses the connected workspace's credits | Yes | It is spending, so it needs your OK. The connector makes 2 takes by default; the jobs file is set to 1. |

Sources (third-party summaries; check [elevenlabs.io/pricing](https://elevenlabs.io/pricing) before paying):
[Cartesia](https://www.cartesia.ai/learn/elevenlabs-pricing), [Dupple](https://dupple.com/learn/is-elevenlabs-free),
[Stacknota](https://stacknota.com/en/ai-voice-video/elevenlabs-pricing/).

**Commercial use:** a monetised YouTube channel counts as commercial. The audio for the real video must be generated
**while a paid plan is active**. Sources say the licence covers audio made during the subscription. The cheapest
paid plan, Starter, is listed at about **$6/month (some sources: $5) for ~30,000 credits**, with a commercial licence
and no attribution. Library voices can carry extra terms from the voice's creator; check Aabo's page before
publishing. These figures come from third-party sites (the ElevenLabs site couldn't be opened from here), so
confirm them on the official pricing page.

## 4. Cost of the final voice-over (eleven_multilingual_v2, 1 credit per character)

Rate confirmed with free price checks today: 407 characters → 407 credits → $0.0407. That is **$0.01 per 100
credits**, the price the connected workspace shows. Full table per file: `final-voice-cost.csv`.

| File | Characters = credits | $ (1 take) |
|---|---|---|
| s01 hook | 175 | 0.02 |
| s02 disclosure | 262 | 0.03 |
| s03 #10 Rubbermaid | 558 | 0.06 |
| s04 #9 Zulay | 531 | 0.05 |
| s05 #8 KitchenAid | 640 | 0.06 |
| s06 #7 Microplane | 566 | 0.06 |
| s07 #6 OXO brush | 654 | 0.07 |
| s08 #5 PowerLix | 438 | 0.04 |
| s09 #4 Fullstar | 606 | 0.06 |
| s10 #3 OXO spinner | 585 | 0.06 |
| s11 #2 TP19H | 729 | 0.07 |
| s12 #1 Dash | 681 | 0.07 |
| s13 wrap-up | 266 | 0.03 |
| **Long video total** | **6,691** | **0.67** |
| short1 Dash | 609 | 0.06 |
| short2 Microplane | 693 | 0.07 |
| short3 TP19H | 680 | 0.07 |
| **3 Shorts total** | **1,982** | **0.20** |
| **Everything, 1 take** | **8,673** | **0.87** |
| + voice test (passage + pronunciation lines) | 1,018 | 0.10 |
| + one re-record of the longest scene | 729 | 0.07 |
| **Total budget** | **10,420** | **≈ 1.04** |
| If 2 takes per file (connector default) | 17,346 for the final files | 1.73 |

Character counts include the pronunciation spellings. A different Zulay/TP19H/Microplane version changes the totals
by only a few characters.

**In money terms for commercial use:** the credits fit easily inside one month of Starter (30,000 credits).
Realistic cost: **one Starter month (≈ $5–6)**, which also covers re-takes. The $0.87 above is the workspace's
per-credit price. It does **not** replace the paid plan needed for the commercial licence.

## 5. What you need to do to hear the test (choose one)

**A. Free, on your own ElevenLabs account (recommended for the test):**
1. Sign in at elevenlabs.io (Free plan is fine for a private test) → Text to Speech.
2. Voice: **Aabo – Engaging Confident Explainer Voice**. Model: **Multilingual v2**. Settings: stability 0.50,
   similarity 0.75, style 0, speaker boost on, speed 1.0.
3. Paste `test-passage-voice.txt` and generate once. Then paste `pronunciation-lines.txt` and generate once.
   Together that's about 1,018 of your free credits.
4. Tell me: is the voice right for the channel? Which version (A/B/C) sounds right for Zulay, TP19H and
   Microplane? Do any other names sound wrong?

**B. Through the connector here:** reply with explicit approval for the two jobs in `voice-test-jobs.json`
(1 take each, **1,018 credits ≈ $0.10** from the connected workspace). I'll then generate them and give you the
links. This uses the workspace's credits, and its plan type is unknown to me. If it's a Free plan, the result is
still test-only.

After the test I'll update `config/voice.yaml` with your chosen spellings and set the voice `status: chosen`. The
final voice-over waits until you approve the paid plan and the spend.
