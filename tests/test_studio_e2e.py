#!/usr/bin/env python3
"""End-to-end test of the production studio with FICTIONAL test products and placeholder media.

    python scripts/sfl.py make-test-media        (once)
    python tests/test_studio_e2e.py

Nothing here touches real research, spends credits or uses the network.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sfl_engine.util import Log, SFLError  # noqa: E402
from studio_engine import (pipeline, production_qc, prompts, reference, research, script, seo,  # noqa: E402
                           timeline, voice)
from studio_engine.common import PRODUCTIONS, Production, create_production, save_yaml  # noqa: E402

SLUG = "zz-studio-selftest"
SAMPLES = ROOT / "samples" / "test-media"
TMP = ROOT / "temp" / "selftest-downloads"
PASSED = []


def ok(name, cond, detail=""):
    if not cond:
        raise AssertionError(f"FAILED: {name} {detail}")
    PASSED.append(name)
    print(f"  ✅ {name}")


def cli(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "studio.py"), *args], capture_output=True, text=True,
                          input="yes\n")


def clean():
    for d in (PRODUCTIONS / SLUG, ROOT / "assets" / "video" / SLUG, ROOT / "assets" / "images" / SLUG, TMP,
              ROOT / "references" / "zz-test-reference"):
        if d.exists():
            shutil.rmtree(d)


def fixture_products():
    src = {"S1": {"url": "https://example.com/test-review", "type": "third_party", "publisher": "Example (TEST)",
                  "title": "Fictional review page", "accessed": "2026-11-03"},
           "S2": {"url": "https://example.com/test-store", "type": "retailer", "publisher": "Example store (TEST)",
                  "title": "Fictional store", "accessed": "2026-11-03"},
           "SA": {"url": "https://www.amazon.com/dp/B0TEST0001", "type": "amazon_search_index",
                  "publisher": "Amazon.com (TEST)", "title": "Fictional Amazon page", "accessed": "2026-11-03"}}

    def f(v, s="S1", verified=False):
        return {"value": v, "verified": verified, "sources": [s], "as_of": "2026-11-03"}

    prods = []
    for i, (n, look) in enumerate([("Alpha", "a round green silicone tool"), ("Bravo", "a slim steel tool"),
                                   ("Charlie", "a small white plastic gadget")], 1):
        prods.append({
            "id": f"t{i}", "rank": i, "status": "shortlisted", "category": "TEST",
            "name": f(f"TEST Product {n} (fictional)"), "short_name": f"Test {n}", "brand": f("TestBrand"),
            "asin": f(f"B0TEST000{i}", "SA"), "amazon_url": f(f"https://www.amazon.com/dp/B0TEST000{i}", "SA"),
            "price_amazon": {"value": None, "verified": False, "sources": [], "as_of": None},
            "prices_third_party": [{"value": 10 + i, "currency": "USD", "seller": "Example store", "source": "S2",
                                    "as_of": "2026-11-03"}],
            "rating_amazon": f(4.5, "SA"), "review_count_amazon": f(1000 * i, "SA"),
            "features": [{"text": "it does one simple job quickly", "source": "S1"}],
            "pros": [{"text": "people like how easy it is to clean", "source": "S1"}],
            "cons": [{"text": "some find it smaller than expected", "source": "S1"}],
            "best_for": "small kitchens", "why_selected": "fictional test item", "angle": "a fictional everyday problem",
            "visual_description": look, "broll_use": "on a wooden board", "broll_problem": "a messy counter",
            "shorts_hook": f"Test hook {n}"})
    return {"research": {"topic": "TEST", "market": "Amazon USA", "researched_on": "2026-11-03",
                         "researcher": "test fixture"}, "sources": src, "products": prods}


def main():
    clean()
    log = Log("selftest")
    print("1. production + research")
    prod = create_production("Studio Self-Test (fictional products)", slug=SLUG)
    prod.meta["products_wanted"] = 3
    prod.meta["music"] = {"file": "samples/test-media/music_placeholder_generated.wav", "license": "generated"}
    prod.save()
    research.save_research(prod, fixture_products())
    r = cli("research-report", SLUG)
    ok("research-report runs without errors", r.returncode == 0, r.stdout + r.stderr)
    for fn in ("report.md", "shortlist.md", "amazon-verification.csv", "amazon-verification.md"):
        ok(f"{fn} written", prod.p("research", fn).exists())
    sl = prod.p("research", "shortlist.md").read_text()
    ok("shortlist marks third-party rating as unverified", "(unverified)" in sl)
    # bad data is caught
    bad = fixture_products()
    bad["products"][0]["rating_amazon"]["verified"] = True  # verified without an Amazon source
    bad["products"][1]["features"][0]["source"] = None
    errs = [m for l, m in research.validate(bad, 3) if l == "error"]
    ok("validator rejects 'verified' without Amazon source", any("marked verified" in e for e in errs))
    ok("validator rejects unsourced feature", any("has no source" in e for e in errs))
    bad2 = fixture_products()
    bad2["products"][2]["rating_amazon"]["sources"] = ["S1"]  # third-party figure placed in an Amazon field
    errs2 = [m for l, m in research.validate(bad2, 3) if l == "error"]
    ok("validator keeps third-party data out of Amazon fields", any("may only cite Amazon pages" in e for e in errs2))
    sl_lines = [ln for ln in sl.splitlines() if ln.startswith("| ") and "**#" in ln]
    ok("shortlist is in countdown order (#3 first, #1 last)", "**#3**" in sl_lines[0] and "**#1**" in sl_lines[-1])
    # approval gate before verification import
    r = cli("draft-script", SLUG)
    ok("script refused before approval", r.returncode != 0 and "Approve" in (r.stderr + r.stdout))

    print("2. verification sheet round trip")
    import csv
    path = prod.p("research", "amazon-verification.csv")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    row_t1 = next(r for r in rows if r["product_id"] == "t1")  # sheet is in countdown order
    row_t1.update({"correct_product_yes_no": "yes", "available_in_us_yes_no": "yes", "amazon_price_usd": "$12.99",
                    "amazon_rating": "4.6", "amazon_rating_count": "2,345", "asin_confirmed_or_corrected": "B0TEST0001",
                    "checked_on_yyyy_mm_dd": "2026-11-03"})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    research.import_verification(prod, log)
    data = research.load_research(prod)
    t1 = data["products"][0]
    ok("owner-checked price is verified", t1["price_amazon"]["verified"] and t1["price_amazon"]["value"] == 12.99)
    ok("owner-checked rating count parsed", t1["review_count_amazon"]["value"] == 2345)
    ok("other products stay unverified", not data["products"][1]["rating_amazon"]["verified"])
    ok("data still valid after import", not [m for l, m in research.validate(data, 3) if l == "error"])
    r = cli("research-report", SLUG)
    r = cli("approve-products", SLUG)
    ok("approve-products", r.returncode == 0, r.stderr)

    print("3. script")
    r = cli("draft-script", SLUG)
    ok("draft-script + check pass", r.returncode == 0, r.stdout + r.stderr)
    s = script.load_script(prod)
    ok("5 scenes (hook + 3 products + wrap-up)", len(s["scenes"]) == 5)
    ok("3 Shorts planned", len(s["shorts"]) == 3)
    t1_scene = next(x for x in s["scenes"] if x.get("product") == "t1")
    ok("verified rating used as a registered claim", "4.6 stars" in t1_scene["narration"] and t1_scene["claims"])
    t2_scene = next(x for x in s["scenes"] if x.get("product") == "t2")
    ok("unverified rating NOT spoken", "stars" not in t2_scene["narration"])
    ok("no prices spoken", "$" not in json.dumps([x["narration"] for x in s["scenes"]]))
    # guards
    ref_dir = ROOT / "references" / "zz-test-reference" / "transcripts"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "abcdefghijk.txt").write_text("0:00 honestly this little thing changed the way my whole family cooks "
                                             "dinner every night\n0:05 and you need one", encoding="utf-8")
    s2 = json.loads(json.dumps(s))
    s2["scenes"][2]["narration"] += " I tested it for a month. It costs $19.99 and has 4.8 stars. " \
                                    "This little thing changed the way my whole family cooks dinner."
    issues, _ = script.check(prod, s2)
    msgs = " ".join(m for l, w, m in issues if l == "error")
    ok("catches testing claim", "I tested" in msgs)
    ok("catches spoken price", "price" in msgs)
    ok("catches unverified star rating", "star rating" in msgs)
    ok("catches copied reference phrasing", "match reference" in msgs)

    print("4. prompts + clip import")
    r = cli("prompts", SLUG)
    ok("prompts written", r.returncode == 0 and prod.p("prompts", "higgsfield-prompts.md").exists(), r.stderr)
    md = prod.p("prompts", "higgsfield-prompts.md").read_text()
    ok("prompts say nothing generated", "Nothing here has been generated" in md and "not generated/imported" in md)
    ok("vertical versions for Shorts scenes", "9:16" in md)
    TMP.mkdir(parents=True, exist_ok=True)
    allshots = prompts.shots(prod)
    vids = [SAMPLES / "clip_a_left_object.mp4", SAMPLES / "clip_b_with_sound.mp4", SAMPLES / "clip_d_very_short.mp4"]
    for k, sh in enumerate(allshots):
        if sh["type"] == "product_photo":
            shutil.copy(SAMPLES / "image_2_cutout.png", TMP / f"Download {sh['id'].upper()} final.png")
        else:
            shutil.copy(vids[k % 3], TMP / f"higgsfield_{sh['id']}_1730000.mp4")
    shutil.copy(vids[0], TMP / "random_name_without_id.mp4")
    done, unmatched = prompts.import_clips(prod, TMP, log)
    ok("every shot imported by id", len(done) == len(allshots), f"{len(done)} vs {len(allshots)}")
    ok("file without shot id reported, not imported", any("random_name" in u for u in unmatched))
    ok("downloads left untouched", (TMP / "random_name_without_id.mp4").exists())

    print("5. voice")
    pack = voice.export_pack(prod, log)
    ok("voice jobs exported with character count", pack["total_characters"] > 100 and len(pack["jobs"]) == 5)
    cfgv = voice.voice_cfg()
    ok("pronunciation fix applied to voice text only", voice.speakable("The OXO press", cfgv) == "The ox-oh press"
       and "OXO" in "The OXO press")
    vdl = TMP / "voice"
    vdl.mkdir()
    for k, sc in enumerate(s["scenes"]):
        shutil.copy(SAMPLES / f"voice_0{(k % 4) + 1}_placeholder.wav", vdl / f"SmartFinds_{sc['id']}_take1.wav")
    # synthetic ElevenLabs-format timing (format test, not real API output)
    words = [{"text": w, "start": i * 0.4, "end": i * 0.4 + 0.35, "type": "word"} for i, w in
             enumerate("This is a word timing test. It checks subtitle alignment.".split())]
    (vdl / "s01.words.json").write_text(json.dumps({"words": words}))
    voice.import_voice(prod, vdl, log)
    ok("voice imported for all scenes", all(voice.scene_audio(prod, sc["id"]) for sc in s["scenes"]))
    voice.align(prod, log)
    srt = prod.p("voice", "s01.srt").read_text()
    ok("word timings -> SRT split at sentences", "test." in srt and "00:00:02,400" in srt, srt)
    al = {"alignment": {"characters": list("Hi there."), "character_start_times_seconds": [i * 0.1 for i in range(9)],
                        "character_end_times_seconds": [i * 0.1 + 0.08 for i in range(9)]}}
    ok("ElevenLabs TTS alignment format parsed", [w for w, a, b in voice.parse_word_timings(al)] == ["Hi", "there."])
    req = voice.api_request("Hello", voice.voice_cfg())
    ok("API request built for the configured voice", "KeU8nqWFDbaoi0QVUjD3/with-timestamps" in req["url"])
    r = cli("tts", SLUG)
    ok("tts is a dry run without --confirm-spend", "DRY RUN" in r.stdout and r.returncode == 0, r.stdout + r.stderr)

    print("6. render (long + 3 Shorts) + thumbnails + SEO + QC")
    status, items = pipeline.render(prod, log)
    ok("production QC is not FAIL", status != "FAIL", "\n".join(f"{a} {b} {c}" for a, b, c in items if a == "error"))
    for k in range(1, 4):
        ok(f"Short {k} rendered", (ROOT / "output" / "shorts" / f"{SLUG}-short-{k}.mp4").exists())
    ok("2 thumbnails", len(list(prod.p("thumbnails").glob("*.jpg"))) == 2)
    seoj = json.loads(prod.p("seo", "youtube.json").read_text())
    ok("SEO chapters start at 0:00 and are real (voice present)", seoj["chapters"][0][0] == 0
       and not seoj["chapters_estimated"])
    ok("SEO has disclosure", "Amazon Associate" in seoj["description"])
    rep = prod.p("reports", "production-qc.md").read_text()
    ok("QC separates automated and human review", "Part A" in rep and "Part B" in rep and "- [ ]" in rep)
    ok("human review not marked automatically", "NOT DONE" in rep)
    ok("export integrity check ran", "every frame decodes" in rep)

    plan_md = prompts.write_visual_plan(prod, log)
    ok("visual plan written with shots and overlays", "| Shot |" in plan_md.read_text() and "badge" in plan_md.read_text())
    from studio_engine import package
    pk = package.write(prod, log)
    for fn in ("shorts-scripts.md", "voiceover-sections.md", "thumbnail-concepts.md", "production-checklist.md"):
        ok(f"package {fn}", (pk / fn).exists())

    print("7. reference analysis")
    reference.new_reference("zz-test-reference", "https://www.youtube.com/@example",
                            ["https://www.youtube.com/watch?v=abcdefghijk"], log)
    rf = ROOT / "references" / "zz-test-reference" / "reference.yaml"
    import yaml
    d = yaml.safe_load(rf.read_text())
    d["videos"][0].update({"title": "7 Kitchen Tools That Actually Help (2026)", "published": "2026-10-01",
                           "duration": "0:10", "views": 1200,
                           "description": "0:00 Intro\n0:03 #2 Tool\n0:06 #1 Tool"})
    d["videos"].append({"url": "https://youtu.be/bbbbbbbbbbb", "video_id": "bbbbbbbbbbb",
                        "title": "Are These Gadgets Worth It?", "published": "2026-10-08", "duration": "8:20",
                        "views": 5000})
    d["videos"].append({"url": "https://youtu.be/ccccccccccc", "video_id": "ccccccccccc",
                        "title": "10 GENIUS Amazon Finds", "published": "2026-10-15", "duration": "45", "views": 900})
    save_yaml(rf, d)
    res = reference.analyze("zz-test-reference", log, [str(ROOT / "output" / "long-videos" / f"{SLUG}.mp4")])
    rep = (ROOT / "references" / "zz-test-reference" / "report.md").read_text()
    ok("reference report has data/manual labels", "📊" in rep and "👁️ Requires manual visual review" in rep)
    ok("title statistics computed", res["videos"] == 3 and "Contain a number" in rep)
    ok("cuts per minute measured from local file", res["measured"][0]["cuts"] >= 1, str(res.get("measured")))
    ok("transcript pace measured", res.get("wpm"))

    print(f"\nALL {len(PASSED)} CHECKS PASSED")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, SFLError) as e:
        print(f"\n{e}")
        sys.exit(1)
