#!/usr/bin/env python3
"""Independent tests for the editor features added for kitchen-gadgets-10 (2026-11-03):

  A. graphic cards            (sfl_engine: config -> plan -> graphics -> render)
  B. per-photo camera moves   (studio timeline mapping + sfl_engine zoom/focus + render)
  C. dedicated Shorts audio   (script helpers -> voice pack/import -> timeline -> load_shorts -> render)
  D. SEO pack fixes           (display names + standalone Shorts descriptions)
  E. safety guards            (withdrawn claims, stale voice, timeline/script mismatch)

Uses FICTIONAL products and the placeholder files in samples/test-media only. No network, no credits.
Renders are drafts written to temp/feature-tests/ (never to output/).

    python scripts/sfl.py make-test-media        (once)
    python tests/test_editor_features.py
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from sfl_engine.builder import load_shorts, render_project  # noqa: E402
from sfl_engine.config import load_timeline, parse_clip, parse_scene, load_brand  # noqa: E402
from sfl_engine.graphics import Graphics  # noqa: E402
from sfl_engine.plan import make_plan  # noqa: E402
from sfl_engine.util import Log, probe  # noqa: E402
from studio_engine import prompts, production_qc, research, script, seo, timeline, voice  # noqa: E402
from studio_engine.common import PRODUCTIONS, create_production, save_yaml  # noqa: E402
from test_studio_e2e import fixture_products  # noqa: E402

SLUG = "zz-feature-selftest"
SAMPLES = ROOT / "samples" / "test-media"
TMP = ROOT / "temp" / "feature-tests"
PASSED = []
LOG = Log("feature-tests")


def ok(name, cond, detail=""):
    if not cond:
        raise AssertionError(f"FAILED: {name} {detail}")
    PASSED.append(name)
    print(f"  ✅ {name}")


def clean():
    for d in (PRODUCTIONS / SLUG, ROOT / "assets" / "video" / SLUG, ROOT / "assets" / "images" / SLUG, TMP):
        if d.exists():
            shutil.rmtree(d)


def frame_md5(path, t):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-s", "64x64", "-"], capture_output=True).stdout
    import hashlib
    return hashlib.md5(out).hexdigest(), len(out)


# =====================================================================================================
def test_graphic_cards():
    print("A. graphic cards")
    issues = []
    c = parse_clip({"type": "card", "graphic": "pros_cons", "text": "+ fast | - loud", "duration": 3}, "t", issues)
    ok("graphic card clip parses", c.kind == "card" and c.graphic == "pros_cons" and not issues, issues)
    bad = []
    parse_clip({"type": "card", "graphic": "fireworks", "text": "x"}, "t", bad)
    ok("unknown graphic kind is reported", any("graphic 'fireworks' unknown" in m for _, m in bad))
    bad2 = []
    parse_clip({"source": str(SAMPLES / "image_1_square.jpg"), "graphic": "spec"}, "t", bad2)
    ok("graphic on a non-card clip is reported", any("only allowed on card" in m for _, m in bad2))
    sc = parse_scene({"id": "g1", "clips": [{"type": "card", "graphic": "spec", "text": "A · B"}]}, 0, [], load_brand())
    ok("a scene with only a graphic card is NOT turned into a title card", sc.card is None)

    TMP.mkdir(parents=True, exist_ok=True)
    tl = TMP / "graphics.yaml"
    save_yaml(tl, {"project": {"title": "Graphic test", "output": "zz-graphic-test", "format": "long"},
                   "intro": {"enabled": False}, "outro": {"enabled": False},
                   "scenes": [{"id": "a", "duration": 5, "clips": [
                       {"source": str(SAMPLES / "image_1_square.jpg"), "duration": 2},
                       {"type": "card", "graphic": "pros_cons", "duration": 3,
                        "text": "+ shuts itself off, easy cleanup | - loud buzzer"}]},
                       {"id": "b", "duration": 3, "clips": [
                           {"type": "card", "graphic": "spec", "duration": 3, "text": "Reading in ~3-4 s · per manual"}]}]})
    proj = load_timeline(tl)
    ok("timeline with graphic cards loads without errors", not [m for l, m in proj.issues if l == "error"], proj.issues)
    plan = make_plan(proj, LOG, allow_missing=True)
    gov = [o for o in plan.overlays if o["type"] == "card_graphic"]
    ok("planner creates one text overlay per graphic segment", len(gov) == 2, gov)
    a0 = gov[0]
    ok("pros/cons text starts when its card starts (~2 s), not at scene start", 1.9 <= a0["t0"] <= 2.3, a0)
    ok("graphic text ends before the next scene's transition", a0["t1"] <= 5.0, a0)
    g = Graphics(plan)
    g.build()
    ass = g.write(TMP / "graphics.ass").read_text()
    ok("pros/cons card draws both neutral labels (no buyer attribution)", "THE GOOD" in ass and "THE CATCH" in ass)
    ok("pros/cons items are drawn", "shuts itself off" in ass and "loud buzzer" in ass)
    ok("spec card headline + line drawn", "Reading in ~3-4 s" in ass and "per manual" in ass)
    proj = load_timeline(tl)
    proj.output = TMP / "zz-graphic-test.mp4"
    out = render_project(proj, LOG, overwrite=True, draft=True)
    info = probe(out) if out else {}
    ok("graphic-card video renders (draft)", out and out.exists() and abs(info["duration"] - 8.0) < 0.6, info)
    h1, n1 = frame_md5(out, 1.0)
    h2, n2 = frame_md5(out, 3.5)
    ok("card frames differ from photo frames (card actually shown)", n1 > 0 and h1 != h2)


# =====================================================================================================
def test_photo_moves():
    print("B. per-photo camera moves")
    img = SAMPLES / "image_1_square.jpg"
    full = timeline.photo_clip(img, {"motion": "zoom_in", "crop": "full", "seconds": 4})
    det = timeline.photo_clip(img, {"motion": "pan_right", "crop": "latch", "seconds": 3})
    ok("crop 'full' -> whole product (contain, no extra zoom)", full["fit"] == "contain" and "zoom" not in full
       and full["motion"] == "zoom_in" and full["duration"] == 4.0)
    ok("detail crop -> cover + base zoom + focus", det["fit"] == "cover" and det["zoom"] == timeline.DETAIL_ZOOM
       and det["motion"] == "pan_right" and det["focus_x"] == 0.5 and det["duration"] == 3.0)
    ok("unknown motion falls back to zoom_in", timeline.photo_clip(img, {"motion": "spin"})["motion"] == "zoom_in")
    bad = []
    parse_clip({"source": str(img), "zoom": 4}, "t", bad)
    ok("zoom outside 1.0-2.5 is reported", any("zoom must be between" in m for _, m in bad))
    tl = TMP / "photos.yaml"
    save_yaml(tl, {"project": {"title": "Photo moves", "output": "zz-photo-test", "format": "long"},
                   "intro": {"enabled": False}, "outro": {"enabled": False},
                   "scenes": [{"id": "p", "duration": 6, "clips": [{**full, "source": str(img), "duration": 3},
                                                                   {**det, "source": str(img), "duration": 3}]}]})
    proj = load_timeline(tl)
    plan = make_plan(proj, LOG, allow_missing=True)
    k = [s.key for ps in plan.scenes for s in ps.segments]
    ok("the two moves of the same photo are different render jobs (cache keys)", len(set(k)) == 2, k)
    proj.output = TMP / "zz-photo-test.mp4"
    out = render_project(proj, LOG, overwrite=True, draft=True)
    ok("photo-move video renders (draft)", out and out.exists() and abs(probe(out)["duration"] - 6.0) < 0.5)
    a, _ = frame_md5(out, 2.8)
    b, _ = frame_md5(out, 3.2)
    ok("first and second move look different (full vs detail crop)", a != b)


# =====================================================================================================
def fixture_script():
    def shot(id_, **kw):
        return {"id": id_, **kw}
    return {
        "title": "Feature self-test (fictional)", "status": "TEST", "video_type": "research_based",
        "words_per_minute": 155,
        "scenes": [
            {"id": "s01", "role": "hook", "narration": "Three small fictional gadgets that fix tiny jobs.",
             "on_screen": {"title": "Feature test"}, "shots": [shot("s01-a", type="ai_broll", prompt="a kitchen")]},
            {"id": "s02", "role": "product", "rank": 1, "product": "t1",
             "narration": "Number one is Test Alpha. It does one simple job quickly, and people like how easy it is "
                          "to clean. Some find it smaller than expected.",
             "on_screen": {"badge": "#1", "lower_third": "Test Alpha"},
             "shots": [shot("s02-a", type="ai_broll", prompt="a round green tool on a board"),
                       shot("s02-photo", type="product_photo", product="t1", motion="zoom_in", crop="full", seconds=3),
                       shot("s02-photo2", type="product_photo", product="t1", motion="pan_left", crop="detail", seconds=3),
                       shot("s02-b", type="stock", search="tidy counter", seconds=4),
                       shot("s02-c", type="graphic", graphic="pros_cons", text="+ quick, easy to clean | - small",
                            seconds=3)]},
            {"id": "s03", "role": "wrapup", "narration": "That's the list. Subscribe for more research-based finds.",
             "on_screen": {"cta": "Links in the description"}, "shots": [shot("s03-a", type="stock", search="window")]},
        ],
        "shorts": [
            {"id": "short1", "product": "t1", "use_scenes": ["s02"], "hook": "Tiny job, fixed", "title": "Alpha Short",
             "narration": "Stop doing this tiny job the slow way. Test Alpha does it quickly, and people like how easy "
                          "it is to clean. One catch: some find it smaller than expected. We did not test it "
                          "ourselves; this is from fictional reviews. Subscribe for more research-based finds.",
             "shots": [shot("short1-a", type="ai_broll", aspect="9:16", prompt="a green tool, vertical"),
                       shot("short1-b", type="product_photo", product="t1", motion="zoom_in", crop="full", seconds=3),
                       shot("short1-c", type="graphic", graphic="pros_cons", text="+ quick | - small", seconds=3),
                       shot("short1-d", type="stock", aspect="9:16", search="counter", seconds=3),
                       shot("short1-e", type="graphic", graphic="cta", text="Comment · Subscribe", seconds=2)]},
            {"id": "short2", "product": "t1", "use_scenes": ["s02"], "hook": "Legacy short", "title": "Legacy"},
        ],
    }


def make_fixture_production():
    prod = create_production("Feature Self-Test (fictional)", slug=SLUG)
    prod.meta["products_wanted"] = 3
    prod.meta["withdrawn_claims"] = ["Test Kitchen says"]
    prod.meta["seo"] = {"titles": ["Feature test title"], "description_intro": "Fictional test video.",
                        "tags": ["test"], "display_names": {"t1": "Test Alpha (display name)"}}
    prod.save()
    research.save_research(prod, fixture_products())
    prod.meta["approved_products"] = ["t1", "t2", "t3"]
    prod.save()
    prod.mark("products_approved", "test")
    save_yaml(prod.p("script", "script.yaml"), fixture_script())
    prod.mark("script", "test")
    prod.image_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SAMPLES / "image_1_square.jpg", prod.image_dir / "t1.jpg")
    return prod


def test_dedicated_shorts(prod):
    print("C. dedicated Shorts (own narration + voice)")
    s = script.load_script(prod)
    units = script.voice_units(s)
    ok("voice units = 3 scenes + 1 dedicated Short (legacy Short has no own voice)",
       [u["id"] for u in units] == ["s01", "s02", "s03", "short1"])
    issues, _ = script.check(prod, s)
    errs = [(w, m) for l, w, m in issues if l == "error"]
    ok("fixture script passes the checks", not errs, errs)
    pack = voice.export_pack(prod, LOG)
    ok("voice pack includes the Short's own text", any(j["scene"] == "short1" and j["kind"] == "short"
                                                       for j in pack["jobs"]))
    ok("voice/text/short1.txt written", prod.p("voice", "text", "short1.txt").exists())
    dl = TMP / "downloads"
    dl.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SAMPLES / "voice_01_placeholder.wav", dl / "short1_take.wav")
    shutil.copy2(SAMPLES / "voice_02_placeholder.wav", dl / "s02.wav")
    n = voice.import_voice(prod, dl, LOG)
    ok("import-voice recognises short1 + s02 files", n == 2 and voice.scene_audio(prod, "short1") is not None)
    ok("imported voice is stamped with its narration text", prod.p("voice", "short1.text-md5").exists())
    ok("no stale voice right after import", voice.stale_voice(prod, units) == [])

    path, spath, missing = timeline.build(prod, LOG, placeholders=True)
    sdoc = json.loads(json.dumps(__import__("yaml").safe_load(spath.read_text())))
    ded, legacy = sdoc["shorts"]
    ok("dedicated Short has its own narration in shorts.yaml", ded.get("narration", "").startswith("Stop doing"))
    ok("dedicated Short uses voice/short1.*", ded["scenes"][0].get("voice", "").endswith("short1.wav"))
    ok("dedicated Short uses its own shots (graphic card included, cta card removed)",
       any(c.get("graphic") == "pros_cons" for c in ded["scenes"][0]["clips"])
       and not any(c.get("graphic") == "cta" for c in ded["scenes"][0]["clips"]))
    ok("dedicated Short ending = its own CTA, never 'Full top … on the channel'",
       ded["cta"]["text"] == "Comment · Subscribe" and "Full top" not in spath.read_text().split("Legacy")[0])
    ok("legacy Short still re-uses the long-video scene", legacy["scenes"][0]["id"] == "s02"
       and "Full top" in legacy["cta"]["text"])
    ok("long timeline records which script it was built from",
       __import__("yaml").safe_load(path.read_text())["project"]["source_script_md5"])
    tl = __import__("yaml").safe_load(path.read_text())
    s02 = next(x for x in tl["scenes"] if x["id"] == "s02")
    photos = [c for c in s02["clips"] if str(c.get("source", "")).endswith("t1.jpg")]
    ok("long timeline: two different moves of the product photo", len(photos) == 2 and photos[0]["fit"] == "contain"
       and photos[1]["fit"] == "cover" and photos[1]["motion"] == "pan_left")
    ok("long timeline: graphic card present, not reported missing",
       any(c.get("graphic") == "pros_cons" for c in s02["clips"]) and not any("s02-c" in m for m in missing))

    projs = load_shorts(spath)
    ok("shorts.yaml loads (2 Shorts)", len(projs) == 2 and not [m for p in projs for l, m in p.issues if l == "error"])
    p1 = projs[0]
    p1.output = TMP / "zz-short1.mp4"
    out = render_project(p1, LOG, overwrite=True, draft=True)
    info = probe(out) if out else {}
    vlen = probe(SAMPLES / "voice_01_placeholder.wav")["audio_duration"]
    ok("dedicated Short renders vertical 1080x1920 (draft)", out and (info["width"], info["height"]) == (1080, 1920), info)
    ok("Short length follows its own voice file", info and vlen <= info["duration"] <= vlen + 2.5,
       (vlen, info.get("duration")))

    rows = prompts.write_prompts(prod, LOG)
    types = {r["shot_id"]: r["type"] for r in rows}
    ok("prompts: stock shots are listed as stock, not AI", types.get("s02-b") == "stock" and types.get("short1-d") == "stock")
    ok("prompts: graphic cards are not sent to Higgsfield", "s02-c" not in types and "short1-c" not in types)
    vcopies = sorted(r["shot_id"] for r in rows if r["shot_id"].endswith("-v"))
    ok("prompts: dedicated Short AI clip is 9:16; '-v' copies only for the scene a legacy Short re-uses",
       any(r["shot_id"] == "short1-a" and r["aspect"] == "9:16" for r in rows) and vcopies == ["s02-a-v"], vcopies)
    return path


def test_seo(prod):
    print("D. SEO pack")
    pack = seo.build(prod, LOG)
    ok("description uses the display name from production.yaml", "Test Alpha (display name)" in pack["description"]
       and "TEST Product Alpha (fictional)" not in pack["description"])
    sd = {x["id"]: x["description"] for x in pack["shorts"]}
    ok("standalone Short description has the research note, no 'part of our'",
       "did not test" in sd["short1"] and "part of our" not in sd["short1"])
    ok("legacy Short description unchanged", "part of our" in sd["short2"])


def test_guards(prod, tl_path):
    print("E. safety guards")
    s = script.load_script(prod)
    s2 = copy.deepcopy(s)
    s2["scenes"][1]["narration"] += " Test Kitchen says it won."
    errs = [m for l, w, m in script.check(prod, s2)[0] if l == "error"]
    ok("withdrawn claim in a scene is blocked", any("WITHDRAWN" in m for m in errs))
    s3 = copy.deepcopy(s)
    s3["shorts"][0]["narration"] += " It is number one in our full list."
    errs = [m for l, w, m in script.check(prod, s3)[0] if l == "error"]
    ok("dedicated Short that refers to the long video / rank is blocked", any("must not refer" in m for m in errs))
    s4 = copy.deepcopy(s)
    s4["shorts"][0]["narration"] += " I tested it for a week."
    errs = [m for l, w, m in script.check(prod, s4)[0] if l == "error"]
    ok("testing claim in a dedicated Short is blocked", any("research-based" in m for m in errs))
    # stale voice: change the Short's text after the voice was imported
    save_yaml(prod.p("script", "script.yaml"), s3 if False else {**s, "shorts": [
        {**s["shorts"][0], "narration": s["shorts"][0]["narration"].replace("quickly", "fast")}, s["shorts"][1]]})
    stale = voice.stale_voice(prod, script.voice_units(script.load_script(prod)))
    ok("voice recorded from older text is detected", stale == ["short1"], stale)
    qc_items = []

    class L2:
        def info(self, *a, **k): pass
        def warn(self, *a, **k): pass
        def debug(self, *a, **k): pass
    production_qc.run(prod, L2(), decode=False)
    rep = prod.p("reports", "production-qc.md").read_text()
    ok("QC report flags the stale voice file", "OLDER script text" in rep)
    ok("QC report flags the timeline built from a different script version", "different script version" in rep)


def test_pronunciation_and_scene_test(prod):
    print("F. pronunciation in voice only + single-scene test file")
    cfg = voice.voice_cfg()
    text = "Number nine is the Zulay press. The TP19H reads fast, and OXO's brush, TempPro, Microplane."
    spoken = voice.speakable(text, cfg)
    ok("voice text uses the pronunciation spellings", all(x in spoken for x in
       (cfg["pronunciations"]["Zulay"], cfg["pronunciations"]["TP19H"], cfg["pronunciations"]["Microplane"])))
    # fake ElevenLabs 'with timestamps' alignment for the SPOKEN text (one char every 0.05 s)
    chars = list(spoken)
    align = {"alignment": {"characters": chars,
                           "character_start_times_seconds": [i * 0.05 for i in range(len(chars))],
                           "character_end_times_seconds": [i * 0.05 + 0.05 for i in range(len(chars))]}}
    words = voice.restore_spelling(voice.parse_word_timings(align), cfg)
    joined = " ".join(w for w, _, _ in words)
    ok("subtitle words get the ORIGINAL spelling back", joined == text, joined)
    tp = next(w for w in words if w[0].startswith("TP19H"))
    ok("a multi-word alias becomes one word spanning its whole timing",
       tp[2] - tp[1] > 0.05 * (len(cfg["pronunciations"]["TP19H"]) - 1))
    for k in ("Zulay", "TP19H", "Microplane"):
        ok(f"no pronunciation spelling for {k} left in subtitles", cfg["pronunciations"][k] not in joined)
    # srt written by align() for an imported scene
    prod.p("voice", "s02.words.json").write_text(json.dumps(align), encoding="utf-8")
    voice.align(prod, LOG)
    srt = prod.p("voice", "s02.srt").read_text()
    ok("align() writes subtitles with Zulay / TP19H / Microplane spelled correctly",
       "Zulay" in srt and "TP19H" in srt and "Microplane" in srt and "Soo-lay" not in srt and "nineteen" not in srt)
    # pronunciation dictionary = config
    pack_pls = prod.p("voice", "pronunciation-dictionary.pls")
    voice.export_pack(prod, LOG)
    rules = voice.read_pls(pack_pls.read_text())
    ok("pronunciation-dictionary.pls has exactly the rules in config/voice.yaml",
       rules == {k: v for k, v in cfg["pronunciations"].items() if v and k != v}, rules)
    # single-scene test timeline
    path, missing = timeline.build_scene(prod, LOG, "s02", placeholders=True)
    import yaml as _y
    d = _y.safe_load(path.read_text())
    ok("scene test file has one scene, no intro/outro", len(d["scenes"]) == 1 and d["scenes"][0]["id"] == "s02"
       and d["intro"] == {"enabled": False} and d["outro"] == {"enabled": False})
    ok("scene test uses the imported voice + keeps the scene's text overlays",
       d["scenes"][0].get("voice", "").endswith("s02.wav") and d["scenes"][0].get("overlays"))
    proj = load_timeline(path)
    proj.output = TMP / "zz-scene-test.mp4"
    out = render_project(proj, LOG, overwrite=True, draft=True)
    vlen = probe(SAMPLES / "voice_02_placeholder.wav")["audio_duration"]
    info = probe(out) if out else {}
    ok("single-scene test renders (draft) and follows the voice length",
       out and abs(info["duration"] - vlen) < 2.0, (vlen, info.get("duration")))


def main():
    if not (SAMPLES / "image_1_square.jpg").exists():
        print("Run: python scripts/sfl.py make-test-media")
        return 1
    clean()
    try:
        test_graphic_cards()
        test_photo_moves()
        prod = make_fixture_production()
        tl_path = test_dedicated_shorts(prod)
        test_seo(prod)
        test_pronunciation_and_scene_test(prod)
        test_guards(prod, tl_path)
    finally:
        clean()
    print(f"\nALL {len(PASSED)} FEATURE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
