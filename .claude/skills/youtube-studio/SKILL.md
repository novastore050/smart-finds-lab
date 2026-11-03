---
name: youtube-studio
description: Smart Finds Lab YouTube production studio for faceless Amazon product review videos (long-form + 3 Shorts). Use for any step of a video production in this repository - product research with sourced and verified Amazon data, reference channel analysis, script writing and checking, Higgsfield scene prompts, ElevenLabs voice-over, clip import, FFmpeg editing, Shorts, thumbnails, YouTube SEO and final quality control. Triggers on "new video", "research products", "shortlist", "script", "voiceover", "prompts", "render", "Shorts", "SEO", "QC", "youtube-studio", or a production slug under productions/.
---

# youtube-studio — Smart Finds Lab production workflow

Channel: **Smart Finds Lab** — "Discover. Compare. Buy Smarter." Faceless English videos for US/UK/CA/AU
viewers about Amazon products. Everything runs through two CLIs in this repository:

- `python scripts/studio.py …` — production pipeline (research → QC). Run `--help` for all commands.
- `python scripts/sfl.py …` — the FFmpeg editor the studio drives (do not rebuild it).

## Non-negotiable rules

1. **Never invent product data.** Every value in `research/products.yaml` needs `sources` + `as_of`.
   Values are `verified: true` ONLY when confirmed on the Amazon.com page (owner via the verification
   sheet, or an official Amazon source). Third-party prices/ratings are never presented as Amazon data.
2. **Research-based ≠ tested.** Unless `video_type: hands_on` with a `hands_on` record per scene, scripts
   must not say "I tested", "I bought", "after using it", etc. `check-script` enforces this.
3. **No prices in narration**; star ratings / rating counts only when verified (registered as `claims`).
4. **Spend nothing without explicit owner approval in this conversation**: ElevenLabs generation,
   Higgsfield generation, any paid API, subscriptions, purchases. Free/read-only calls are fine
   (voice list, previews, `estimate_only` / `get_cost` price checks). Show the cost first, then ask.
5. **Never claim something was generated, verified or tested unless it actually was.** Report what is
   still manual. A PASS in automated QC is not a human review.
6. **Never publish or upload.** The owner uploads manually.
7. **No secrets in files or git.** API keys only via environment variables (`ELEVENLABS_API_KEY`,
   `YOUTUBE_API_KEY`). Before any commit run the secret scan (see `reference/qc-and-publish.md`).
8. **Approval gates:** stop and wait for the owner after the research shortlist (before script/voice/clips),
   and before any spending.
9. **Originality:** reference channels are for structure/pacing inspiration only. Never copy scripts,
   footage, thumbnails or music. Their transcripts stay out of git (`references/*/transcripts/`).

10. **Withdrawn claims stay withdrawn:** list them in `production.yaml → withdrawn_claims`; `check-script` blocks them.
    Old files from a replaced script go to `productions/<slug>/superseded/` (never deleted, never used).

## Pipeline (one production = `productions/<slug>/`)

| # | Stage | Command / action | Detail |
|---|---|---|---|
| 1 | Create | `studio.py new "Title" [--slug x]` then set `topic_noun`, `music` in `production.yaml` | |
| 2 | Research | Claude researches with WebSearch and writes `research/products.yaml` | `reference/research-protocol.md` |
| 3 | Report | `studio.py research-report <slug>` → report.md, shortlist.md, amazon-verification.csv/.md | |
| 4 | **STOP** | Owner verifies on Amazon → `import-verification <slug>`; owner runs `approve-products <slug>` | |
| 5 | Script | `studio.py draft-script <slug>` → edit `script/script.yaml` → `check-script <slug>` | `reference/script-guide.md` |
| 6 | Prompts + plan | `studio.py prompts <slug>` → `prompts/higgsfield-prompts.md` + `shotlist.csv`; `studio.py plan <slug>` → `production/visual-plan.md` | `reference/higgsfield-workflow.md` |
| 7 | Voice | `studio.py voice-pack <slug>` → (approved) generate → `import-voice` → `align` | `reference/elevenlabs-voice.md` |
| 8 | Clips | owner generates/downloads → `studio.py import-clips <slug> <folder>` | |
| 8b | Package | `studio.py seo <slug>`, `studio.py thumbnail <slug>`, `studio.py package <slug>` → `production/` (Shorts scripts, voice sections, thumbnail concepts, checklist) | |
| 9 | Render | `studio.py render <slug>` (long + 3 Shorts + thumbnails + SEO + QC); `--draft`, `--placeholders` for previews | |
| 10 | QC | `studio.py qc <slug>` → `reports/production-qc.md` (Part A automated, Part B human) | `reference/qc-and-publish.md` |
| 11 | **STOP** | Owner reviews Part B → `studio.py review-done <slug>` → uploads manually | |

`python scripts/studio.py status <slug>` always shows what is done and the exact next command.

Shot types: `ai_broll`, `stock`, `product_photo` (`motion`, `crop`), `graphic` (`pros_cons`, `spec`, `disclosure`,
`halfway`, `recap`, `note`, `cta`). Shorts with their own `narration` are standalone (voice file `voice/<short-id>.mp3`,
own vertical shots, own ending) and must not mention ranks or the long video (`check-script` enforces this).

Reference channels: `studio.py reference-new <name> --channel URL --video URL…` → owner fills
`references/<name>/reference.yaml` (+ transcripts) → `studio.py reference-analyze <name> [--video-file f]`.
See `reference/reference-analysis.md`.

## How to work in a session

1. Run `python scripts/studio.py status <slug>` (or `ls productions/`) to orient yourself.
2. Do the next stage only. Run its command, read the output, fix problems, re-run.
3. Test what you change (`python tests/test_studio_e2e.py` exercises the whole pipeline with fictional data;
   `python scripts/sfl.py make-test-media` first if `samples/test-media/` is missing).
4. Report to the owner in plain language: what was done, what was tested, what still needs them
   (verification, approvals, generation, review), and the cost of anything proposed.

## Environment notes

- In Claude Code cloud sessions, amazon.com, youtube.com, ElevenLabs and Higgsfield hosts may be blocked
  for scripts and web fetch. WebSearch still works (US results). The ElevenLabs and Higgsfield
  **connectors** (MCP tools) work through Claude, but their output files may not be downloadable into the
  container — tell the owner to download them and use the import commands.
- On the owner's own PC everything runs locally (Python 3.9+, FFmpeg). See `docs/INSTALL.md`.
