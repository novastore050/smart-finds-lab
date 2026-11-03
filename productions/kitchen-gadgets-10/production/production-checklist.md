# Production checklist — 10 Kitchen Gadgets That Actually Make Life Easier

Tick in order. Commands run from the Smart-Finds-Lab folder.

## 1. Facts (before any spending)
- [x] Products approved (Version 4)
- [ ] Fill `research/amazon-verification.csv` on Amazon.com, then `python scripts/studio.py import-verification kitchen-gadgets-10`
- [ ] Resolve every "needs verification" note in `script/script.md` (10 products have no verified Amazon rating)
- [ ] Confirm Zulay pronunciation

## 2. Assets
- [ ] Choose the voice (listen to `productions/_voice-samples/`), set `status: chosen` in `config/voice.yaml`
- [ ] Approve ElevenLabs cost (~8,673 characters per take), generate, then `import-voice` + `align`
- [ ] Generate Higgsfield clips from `prompts/higgsfield-prompts.md` (needs paid credits), then `import-clips kitchen-gadgets-10 <folder>`
- [ ] Add real product photos to `assets/images/<slug>/<product-id>.jpg` (yours or licensed)
- [ ] Add licensed background music and set `music:` in `production.yaml`

## 3. Edit
- [ ] `python scripts/studio.py render kitchen-gadgets-10 --draft` and watch it
- [ ] `python scripts/studio.py render kitchen-gadgets-10` (long video + 3 Shorts + thumbnails + SEO + QC)

## 4. Before upload
- [ ] Part B of `reports/production-qc.md` completed, then `review-done`
- [ ] Amazon Associates tag set in `config/studio.yaml` (if you have one); links checked
- [ ] YouTube: title/description/tags/chapters from `seo/youtube.md`; upload `.srt`; affiliate disclosure;
      altered-content setting if realistic AI scenes; not made for kids
- [ ] Upload manually (nothing is published automatically)
