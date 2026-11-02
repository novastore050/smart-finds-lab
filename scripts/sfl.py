#!/usr/bin/env python3
"""Smart Finds Lab - automated video production.

Run from the Smart-Finds-Lab folder:
    python scripts/sfl.py doctor                         check that everything is installed
    python scripts/sfl.py check  config/timelines/X.yaml  check a timeline (no rendering)
    python scripts/sfl.py build  config/timelines/X.yaml  make the long-form video
    python scripts/sfl.py shorts config/shorts/X.yaml     make all Shorts in a file
    python scripts/sfl.py --help                          all commands
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sfl_engine import qc  # noqa: E402
from sfl_engine.builder import check_project, load_shorts, render_project  # noqa: E402
from sfl_engine.config import load_timeline  # noqa: E402
from sfl_engine.util import SFLError, Log, probe, rel, resolve  # noqa: E402
from sfl_engine import tools  # noqa: E402


def _print_checks(log, checks, show_ok=True):
    order = {qc.ERR: 0, qc.WARN: 1, qc.INFO: 2, qc.OK: 3}
    for it in sorted(checks.items, key=lambda i: order[i["level"]]):
        if it["level"] == qc.OK and not show_ok:
            continue
        log.info(f"  {qc.ICON[it['level']]} {it['area']}: {it['message']}")


def _missing_files(plan):
    miss = set()
    for ps in plan.scenes:
        for c in ps.scene.clips:
            if c.source and not c.source.exists():
                miss.add(c.source)
        for f in (ps.scene.voice, ps.scene.subtitle_file):
            if f and not f.exists():
                miss.add(f)
    for k in ("voiceover", "music"):
        f = plan.project.audio.get(k)
        if f and not f.exists():
            miss.add(f)
    return sorted(miss)


def cmd_check(a):
    log = Log("check")
    projects = load_shorts(a.file, a.only) if a.shorts else [load_timeline(a.file)]
    worst = 0
    for proj in projects:
        plan, checks = check_project(proj, log)
        log.info(f"\n=== {proj.title} ({proj.fmt}) - planned length {qc.fmt_time(plan.total)} ===")
        _print_checks(log, checks)
        miss = _missing_files(plan)
        if miss:
            log.info(f"\n  Files you still need to provide ({len(miss)}):")
            for m in miss:
                log.info(f"    - {rel(m)}")
        out = proj.output.parent / f"{proj.name}.precheck.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        qc.write_report(out, plan, checks, None, {}, 0)
        log.info(f"\n  RESULT: {checks.status}   (report: {rel(out)})")
        worst = max(worst, 2 if checks.status == "FAIL" else 0)
    return worst


def cmd_build(a):
    log = Log("build")
    proj = load_timeline(a.timeline)
    out = render_project(proj, log, overwrite=a.overwrite, draft=a.draft)
    log.info(f"Full log: {rel(log.path)}")
    return 0 if out else 2


def cmd_shorts(a):
    log = Log("shorts")
    projects = load_shorts(a.file, a.only)
    log.info(f"{len(projects)} Short(s) to make")
    results = []
    for proj in projects:
        try:
            results.append((proj.name, render_project(proj, log, overwrite=a.overwrite, draft=a.draft)))
        except SFLError as e:  # one broken Short must not stop the others
            log.info(f"\nShort '{proj.name}' FAILED: {e}")
            results.append((proj.name, None))
    log.info("\n=== Shorts summary ===")
    for n, r in results:
        log.info(f"  {'OK    ' if r else 'FAILED'} {n}  {rel(r) if r else ''}")
    log.info(f"Full log: {rel(log.path)}")
    return 0 if all(r for _, r in results) else 2


def cmd_info(a):
    info = probe(resolve(a.file))
    for k, v in info.items():
        print(f"{k:>15}: {v}")


def main():
    p = argparse.ArgumentParser(prog="sfl", description="Smart Finds Lab automated video production")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("doctor", help="check installed software")
    s.set_defaults(fn=lambda a: 0 if tools.doctor(Log("doctor")) else 1)

    s = sub.add_parser("check", help="check a timeline or shorts file without rendering")
    s.add_argument("file")
    s.add_argument("--shorts", action="store_true", help="the file is a shorts file")
    s.add_argument("--only", help="only this short (name or number)")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("build", help="render a long-form video from a timeline")
    s.add_argument("timeline")
    s.add_argument("--draft", action="store_true", help="fast low-quality preview")
    s.add_argument("--overwrite", action="store_true", help="replace an existing export instead of making _v2")
    s.set_defaults(fn=cmd_build)

    s = sub.add_parser("shorts", help="render the Shorts listed in a shorts file")
    s.add_argument("file")
    s.add_argument("--only", help="only this short (name or number)")
    s.add_argument("--draft", action="store_true")
    s.add_argument("--overwrite", action="store_true")
    s.set_defaults(fn=cmd_shorts)

    s = sub.add_parser("new", help="create a new timeline from the template")
    s.add_argument("title")
    s.add_argument("--products", type=int, default=10)
    s.set_defaults(fn=lambda a: tools.new_project(a.title, a.products, Log("new")) and 0)

    s = sub.add_parser("make-sfx", help="generate copyright-free sound effects")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=lambda a: tools.make_sfx(Log("sfx"), a.force) and 0)

    s = sub.add_parser("make-test-media", help="generate labelled placeholder media for testing")
    s.set_defaults(fn=lambda a: tools.make_test_media(Log("testmedia")) and 0)

    s = sub.add_parser("import-clips", help="copy downloaded clips (e.g. Higgsfield) into assets/video/<name>")
    s.add_argument("folder")
    s.add_argument("--to", required=True, help="destination name, e.g. kitchen-gadgets-10")
    s.add_argument("--prefix", default="")
    s.set_defaults(fn=lambda a: tools.import_clips(a.folder, a.to, Log("import"), a.prefix) and 0)

    s = sub.add_parser("thumbnail", help="make a 1280x720 thumbnail")
    s.add_argument("--text", required=True)
    s.add_argument("--sub", default="")
    s.add_argument("--badge", default=None)
    s.add_argument("--image")
    s.add_argument("--video")
    s.add_argument("--at", type=float, default=None, help="seconds into --video")
    s.add_argument("--name")
    s.set_defaults(fn=lambda a: tools.make_thumbnail(a.text, a.sub, Log("thumb"), a.image, a.video, a.at,
                                                     a.name, a.badge) and 0)

    s = sub.add_parser("frames", help="save still frames from a video (thumbnail ideas)")
    s.add_argument("video")
    s.add_argument("--count", type=int, default=8)
    s.set_defaults(fn=lambda a: tools.extract_frames(a.video, a.count, Log("frames")) or 0)

    s = sub.add_parser("info", help="show details of a media file")
    s.add_argument("file")
    s.set_defaults(fn=cmd_info)

    a = p.parse_args()
    try:
        sys.exit(a.fn(a) or 0)
    except SFLError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)


if __name__ == "__main__":
    main()
