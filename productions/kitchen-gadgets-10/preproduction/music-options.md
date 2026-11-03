# Music and sound options — kitchen-gadgets-10

Prepared 2026-11-03. **Nothing downloaded, generated or purchased.** The licence pages below couldn't be opened
from this environment (the network blocks them). The terms are summarised from search results and the services'
own help pages as indexed. **Re-read each licence on the day you download** and save a copy (PDF or screenshot)
with the track.

## What we need

- **Long video:** one background track, about 8 minutes (loop or two compatible tracks). Light, upbeat,
  acoustic/lo-fi/"kitchen" feel, roughly 95–115 BPM, **no vocals** (the voice-over must stay clear). The editor ducks
  it under the voice automatically (config/brand.yaml).
- **Shorts:** the same track, or a slightly punchier one. YouTube Shorts use the same rights rules as long videos
  for uploaded audio.
- **Record in `production.yaml → music`:** file, track title, artist, source URL, licence name, download date, and
  any required credit line.

## Recommended sources (genuinely free for monetised YouTube)

| Source | Licence conditions (summary) | Commercial / monetised YouTube | Attribution | Risks / notes |
|---|---|---|---|---|
| **YouTube Audio Library** (YouTube Studio → Audio Library) — **recommended first** | YouTube's own library. Two licence types: the standard licence (no credit) and Creative Commons tracks (credit required). Filter: **"Attribution not required"**. | Yes, for YouTube videos and Shorts; monetisation allowed if the channel is eligible | Not required for standard-licence tracks; CC tracks need the exact credit text in the description | Licensed for use **on YouTube**; ask the artist before using it elsewhere. Sources: [YouTube Help 3376882](https://support.google.com/youtube/answer/3376882?hl=en), [YouTube Help 4523596](https://support.google.com/youtube/answer/4523596) |
| **Pixabay Music** | Pixabay Content License: free, no attribution, may edit; no standalone resale | Yes, but **some tracks are "Content ID registered"** and can trigger automatic claims | Not required | Pick only tracks **without** the Content ID label. Keep the licence/download record to dispute any claim. [Pixabay licence](https://pixabay.com/service/license/) |
| **Uppbeat (Free plan)** | Free tier with a small monthly download limit (sources say about 3). Each download comes with a unique credit code. | Uppbeat says all plans are safe to monetise on YouTube **if the credit is pasted**; paid ads and client work need a paid plan | **Required**: paste the exact credit in the description, a new credit for each video | Limit and plan terms change; check [uppbeat.io/pricing](https://uppbeat.io/pricing). Nothing has been subscribed. |
| **Incompetech (Kevin MacLeod)** | Creative Commons Attribution 4.0 (paid no-credit licence also offered) | Yes | **Required** (title, artist, licence link) | Very widely used, so it can sound generic. Licence not re-checked in this session; confirm on incompetech.com. |
| **Free Music Archive** | Licence varies **per track** (CC BY, CC BY-SA, CC BY-NC, CC0…) | Only tracks **without NC/ND** | Usually required | Never use CC BY-NC tracks on a monetised channel. |
| Mixkit (music) | Mixkit Free licence; commercial use including YouTube | Yes for "Free License" items | Not required | Check each item's licence label; not re-checked this session. |

Paid libraries (Epidemic Sound, Artlist, Musicbed, etc.) cover monetisation with a subscription. They are listed for
completeness only; **nothing has been purchased**.

## Sound effects

| Source | Licence | Recommendation |
|---|---|---|
| **Our own generated SFX**, `assets/sound-effects/generated/` (whoosh, pop, click, ding, riser, swipe), synthesised by the project's FFmpeg tool | Created by us, no third-party rights | ✅ **Use these** (already wired into the editor) |
| YouTube Audio Library sound effects | YouTube licence, no credit | Good backup |
| Freesound.org | Per-sound: **CC0** (free, no credit), **CC BY** (credit required), **CC BY-NC** (not allowed on a monetised channel) | Filter to CC0 only |
| Pixabay sound effects | Pixabay Content License | OK; same Content ID caution as music |

## Recommendation

1. YouTube Audio Library, filter **Attribution not required**, mood "Bright" or "Happy", genre acoustic/lo-fi, no
   vocals, ≥ 3 minutes (the editor loops it). Pick one for the long video and use the same one for the Shorts.
2. Backup: a Pixabay Music track **without** the Content ID label.
3. Keep using our own generated SFX.

Before rendering: put the file in `assets/music/`, fill in `production.yaml → music: {file, license}` with the
details above, and keep the licence copy next to it.
