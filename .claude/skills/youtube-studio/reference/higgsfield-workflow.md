# Higgsfield scene clips (stages 6 + 8)

Current mode: **manual** (owner decision). Do not call Higgsfield generation tools or spend credits
without explicit approval. Read-only checks are fine (`balance`, `models_explore`, `generate_video` with
`get_cost: true`). Status as of 2026-11-03: free plan, 10 credits; one 5 s 1080p Seedance 2.5 clip = 80 credits.

## Prompts

`studio.py prompts <slug>` → `prompts/higgsfield-prompts.md` (organised by scene number) and
`prompts/shotlist.csv`. Each shot has an id (`s03-a`), aspect, length, the prompt with the channel's style
suffix (`config/studio.yaml → visual_style`) and the "avoid" list. Scenes used in Shorts also get a
9:16 version (`s03-a-v`). Product-photo shots (`s03-photo`) are real photos supplied by the owner.

Rules for AI clips: generic b-roll (hands, kitchen, the task, the problem). They must not pretend to show
the exact product — the product photo identifies it. Suggest image-to-video with the owner's product photo
only if the owner accepts the risk of shape distortion, and flag it in Part B of QC.

## Import

Owner saves downloads with the shot id in the name (e.g. `s03-a.mp4`, `Higgsfield_s03-a_123.mp4`) and runs
`studio.py import-clips <slug> <folder>`. Files are COPIED to `assets/video/<slug>/<shot>.mp4`
(photos → `assets/images/<slug>/<product-id>.<ext>`); unmatched files are listed, nothing is overwritten,
a manifest is written. The older `sfl.py import-clips <folder> --to <slug>` also works when names are
already shot ids.

Never report a clip as generated unless the file exists in `assets/video/<slug>/` (the prompts file
and QC show ✅ only for imported files).
