#!/usr/bin/env python3
"""Smart Finds Lab - Production Studio.

Research -> Verification -> Script -> Scene prompts -> Voice-over -> Clip import -> FFmpeg edit
-> Shorts -> Thumbnail -> SEO -> Quality control.   (The editor itself is scripts/sfl.py.)

    python scripts/studio.py new "10 Kitchen Gadgets That Actually Make Life Easier"
    python scripts/studio.py status <slug>          what is done, what is next
    python scripts/studio.py --help                 every command

Nothing here spends money, generates paid media or publishes anything by itself.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sfl_engine.util import SFLError, Log, rel  # noqa: E402
from studio_engine import (package, pipeline, production_qc, prompts, reference, research, script,  # noqa: E402
                           seo, timeline, voice)
from studio_engine.common import Production, create_production  # noqa: E402


def P(a):
    return Production(a.slug)


def cmd_new(a):
    prod = create_production(a.title, "hands_on" if a.hands_on else "research_based", a.slug)
    print(f"Created {rel(prod.dir)}")
    print(f"Next: research products into {rel(prod.p('research', 'products.yaml'))} "
          "(see docs/STUDIO-GUIDE.md), then: python scripts/studio.py research-report " + prod.slug)


def cmd_research_report(a):
    log = Log("research")
    prod = P(a)
    issues = research.write_reports(prod)
    for lvl, m in issues:
        log.info(f"  {'❌' if lvl == 'error' else '⚠️'} {m}")
    errs = sum(1 for l, _ in issues if l == "error")
    prod.mark("research", "products.yaml present")
    if not errs:
        prod.mark("research_report")
    for f in ("report.md", "shortlist.md", "amazon-verification.csv", "amazon-verification.md"):
        log.info(f"  -> {rel(prod.p('research', f))}")
    log.info(f"RESULT: {errs} error(s), {len(issues) - errs} warning(s)")
    return 2 if errs else 0


def cmd_check_script(a):
    log = Log("script")
    prod = P(a)
    issues, st = script.write_markdown(prod)
    for lvl, w, m in issues:
        log.info(f"  {'❌' if lvl == 'error' else '⚠️'} {w}: {m}")
    errs = sum(1 for l, _, _ in issues if l == "error")
    log.info(f"{st['scenes']} scenes, ~{st['est_seconds'] / 60:.1f} min of narration, "
             f"{st['references_checked']} reference transcript(s) compared")
    log.info(f"Readable version: {rel(prod.p('script', 'script.md'))}")
    if errs:
        prod.unmark("script")
        log.info(f"RESULT: {errs} error(s) - fix script/script.yaml and run check-script again")
        return 2
    n_sh = len(script.dedicated_shorts(script.load_script(prod)))
    src = (prod.meta.get("script_source") or {}).get("promoted_from")
    prod.mark("script", f"{st['scenes']} scenes + {n_sh} standalone Shorts" + (f" (promoted from {src})" if src else ""))
    log.info("RESULT: script OK")
    return 0


def cmd_draft(a):
    log = Log("script")
    prod = P(a)
    script.draft(prod, log, force=a.force)
    return cmd_check_script(a)


def cmd_prompts(a):
    prod = P(a)
    prompts.write_prompts(prod, Log("prompts"))
    prod.mark("prompts")


def cmd_qc(a):
    st, _ = production_qc.run(P(a), Log("qc"), decode=not a.fast)
    return 0 if st != "FAIL" else 2


def cmd_review_done(a):
    prod = P(a)
    prod.require("qc", why="Run qc first and read reports/production-qc.md.")
    ans = input("Have you watched the final video and checked every item in Part B of the QC report? (yes/no) ")
    if ans.strip().lower() not in ("y", "yes"):
        print("Not recorded.")
        return 1
    prod.mark("human_review", a.note or "owner approved")
    print("Human review recorded. Upload manually in YouTube Studio when you are ready.")


def cmd_build_timeline(a):
    prod = P(a)
    _, _, missing = timeline.build(prod, Log("timeline"), a.placeholders)
    note = f"{len(missing)} items missing" if missing else "complete"
    prod.mark("timeline", note + (" (placeholder preview)" if a.placeholders else ""))
    return 0


def cmd_seo(a):
    prod = P(a)
    pack = seo.build(prod, Log("seo"))
    prod.mark("seo", "chapters estimated" if pack.get("chapters_estimated") else "")
    return 0


def cmd_status(a):
    pipeline.status(P(a), Log("status"))


def main():
    p = argparse.ArgumentParser(prog="studio", description="Smart Finds Lab production studio")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_, slug=True):
        s = sub.add_parser(name, help=help_)
        if slug:
            s.add_argument("slug", help="production folder name (see productions/)")
        s.set_defaults(fn=fn)
        return s

    s = add("new", cmd_new, "create a production folder", slug=False)
    s.add_argument("title")
    s.add_argument("--slug")
    s.add_argument("--hands-on", action="store_true", help="the owner really tests the products")
    add("status", cmd_status, "show progress and the next step")
    # research
    add("research-report", cmd_research_report, "validate research; write report, shortlist, verification sheet")
    add("import-verification", lambda a: research.import_verification(P(a), Log("verify")) and 0,
        "read the filled Amazon verification sheet")
    s = add("approve-products", lambda a: research.approve(P(a), Log("approve"), a.note) or 0,
            "OWNER: approve the shortlist")
    s.add_argument("--note", default="")
    # script
    s = add("draft-script", cmd_draft, "draft the script from the approved research")
    s.add_argument("--force", action="store_true")
    add("check-script", cmd_check_script, "check honesty, claims, originality and timing")
    # prompts & clips
    add("prompts", cmd_prompts, "write Higgsfield prompts + shot list")
    add("package", lambda a: package.write(P(a), Log("package")) and 0,
        "production package: Shorts scripts, voice sections, thumbnail concepts, checklist")
    add("plan", lambda a: prompts.write_visual_plan(P(a), Log("plan")) and 0,
        "scene-by-scene visual production plan (production/visual-plan.md)")
    s = add("import-clips", lambda a: prompts.import_clips(P(a), a.folder, Log("import")) and 0,
            "copy downloaded clips/photos that have shot ids in their names")
    s.add_argument("folder")
    # voice
    sub.add_parser("voice-samples", help="download FREE previews of the candidate voices").set_defaults(
        fn=lambda a: voice.download_samples(Log("voice")) and 0)
    add("voice-pack", lambda a: voice.export_pack(P(a), Log("voice")) and 0, "export per-scene voice text + jobs")
    s = add("import-voice", lambda a: voice.import_voice(P(a), a.folder, Log("voice")) and 0,
            "copy voice files (s01.mp3 ...) and timing JSON")
    s.add_argument("folder")
    add("align", lambda a: voice.align(P(a), Log("voice")) and 0, "word timings JSON -> exact subtitles (.srt)")
    s = add("tts", lambda a: voice.tts_api(P(a), Log("voice"), a.scene, a.confirm_spend) and 0,
            "ElevenLabs API (dry run unless --confirm-spend; needs ELEVENLABS_API_KEY)")
    s.add_argument("--scene", action="append")
    s.add_argument("--confirm-spend", action="store_true")
    # edit & publish prep
    s = add("build-timeline", cmd_build_timeline,
            "script + assets -> edit/timeline.yaml + edit/shorts.yaml")
    s.add_argument("--placeholders", action="store_true", help="title cards instead of missing clips (preview)")
    s = add("render", lambda a: 0 if pipeline.render(P(a), Log("render"), a.draft, a.skip_shorts,
                                                    a.placeholders)[0] != "FAIL" else 2,
            "long video + 3 Shorts + thumbnails + SEO + QC")
    s.add_argument("--draft", action="store_true")
    s.add_argument("--skip-shorts", action="store_true")
    s.add_argument("--placeholders", action="store_true")
    add("thumbnail", lambda a: pipeline.thumbnails(P(a), Log("thumb")) and 0, "thumbnail variants")
    add("seo", cmd_seo, "titles, description, chapters, tags")
    s = add("qc", cmd_qc, "final production QC report")
    s.add_argument("--fast", action="store_true", help="skip full decode check")
    s = add("review-done", cmd_review_done, "OWNER: record that you reviewed the final video")
    s.add_argument("--note", default="")
    # references
    s = sub.add_parser("reference-new", help="start a reference channel analysis")
    s.add_argument("name")
    s.add_argument("--channel", default="")
    s.add_argument("--video", action="append", default=[])
    s.set_defaults(fn=lambda a: reference.new_reference(a.name, a.channel, a.video, Log("reference")) and 0)
    s = sub.add_parser("reference-fetch", help="optional: fill metadata with YOUTUBE_API_KEY")
    s.add_argument("name")
    s.set_defaults(fn=lambda a: reference.fetch_youtube_api(a.name, Log("reference")) or 0)
    s = sub.add_parser("reference-analyze", help="analysis report for a reference channel")
    s.add_argument("name")
    s.add_argument("--video-file", action="append", default=[])
    s.set_defaults(fn=lambda a: reference.analyze(a.name, Log("reference"), a.video_file) and 0)

    a = p.parse_args()
    try:
        sys.exit(a.fn(a) or 0)
    except SFLError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
