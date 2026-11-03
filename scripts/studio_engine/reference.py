"""Reference channel analysis - learn structure and style from other channels, never copy them.

Data sources (no API key required):
  * reference.yaml   - video URLs + metadata the owner pastes (title, date, length, views, description)
  * transcripts/     - transcripts the owner copies from YouTube's "Show transcript" (kept out of git)
  * --video-file     - a local copy of a video the owner is allowed to analyse (cuts per minute etc.)
  * optional: YOUTUBE_API_KEY in the environment fills metadata automatically (reference-fetch)

Every section of the report says what it is based on. Visual style always needs a human.
Transcripts are also used by check-script to catch copied phrasing.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import statistics as stats
import subprocess
import urllib.parse
from collections import Counter
from pathlib import Path

from sfl_engine.util import ROOT, SFLError, find_tool, probe, rel, slugify

from .common import load_yaml, save_yaml, today

REFS = ROOT / "references"
VID_RE = re.compile(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})")
STOP = set("the a an and or of to in for on with is it this that your you my i are be at by from as these those "
           "how what why best top vs".split())
POWER = ["actually", "genius", "best", "worst", "must", "never", "secret", "only", "really", "finally", "smart",
         "cheap", "under", "amazon", "viral", "tested", "honest", "worth", "every", "need"]
CTA_WORDS = ["subscribe", "comment", "like this video", "link in the description", "links in the description",
             "description below", "bell", "check out"]


def video_id(url: str):
    m = VID_RE.search(url or "")
    return m.group(1) if m else None


def parse_duration(v):
    """Seconds from 754 / '12:34' / '1:02:03' / 'PT12M34S'."""
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
    if m:
        h, mi, se = (int(x or 0) for x in m.groups())
        return float(h * 3600 + mi * 60 + se)
    parts = [float(x) for x in s.split(":")]
    t = 0.0
    for x in parts:
        t = t * 60 + x
    return t


def chapters_from_description(desc: str):
    out = []
    for line in str(desc or "").splitlines():
        m = re.match(r"\s*(?:[-•▶]\s*)?((?:\d{1,2}:)?\d{1,2}:\d{2})\s*[-–—:]?\s*(.+)", line)
        if m:
            out.append((parse_duration(m.group(1)), m.group(2).strip()))
    return out if len(out) >= 3 and out[0][0] == 0 else []


# ---------------------------------------------------------------------------- create / fetch
def new_reference(name: str, channel_url: str = "", video_urls=(), log=None):
    d = REFS / slugify(name)
    (d / "transcripts").mkdir(parents=True, exist_ok=True)
    f = d / "reference.yaml"
    if f.exists():
        raise SFLError(f"{rel(f)} already exists - edit it instead")
    vids = [{"url": u, "video_id": video_id(u), "title": "", "published": "", "duration": "", "views": None,
             "description": ""} for u in video_urls]
    doc = {"name": name, "channel_url": channel_url, "collected_on": today(), "method": "manual",
           "videos": vids,
           "manual_observations": {k: "" for k in ("visual_style", "on_screen_text", "b_roll_and_footage",
                                                   "thumbnail_style", "music_and_sound", "presenter_or_faceless",
                                                   "editing_pace_feel")}}
    save_yaml(f, doc, "# Reference channel. Fill in what you can see on YouTube (or run reference-fetch with an API key).\n"
                      "# duration: '12:34'  published: YYYY-MM-DD  views: number. Paste the description to get chapters.\n"
                      "# Transcripts: YouTube > ... > Show transcript > copy > save as transcripts/<video_id>.txt")
    (d / "README.md").write_text(
        f"# Reference: {name}\n\n1. Fill `reference.yaml` (titles, dates, lengths, views, descriptions).\n"
        "2. Optional: save transcripts as `transcripts/<video_id>.txt` (copied from YouTube's *Show transcript*). "
        "They stay on your computer (not uploaded to GitHub) and are used to analyse hooks/pacing and to make sure "
        "our scripts never copy their wording.\n"
        "3. Optional: `--video-file` with a local copy you are allowed to analyse, to measure cuts per minute.\n"
        f"4. Run: `python scripts/studio.py reference-analyze {slugify(name)}`\n\n"
        "Use references for inspiration only: never reuse their script, footage, thumbnails or music.\n",
        encoding="utf-8")
    if log:
        log.info(f"Created {rel(f)} with {len(vids)} video(s)")
    return f


def fetch_youtube_api(name: str, log):
    """Fill metadata with the YouTube Data API v3 (optional; needs YOUTUBE_API_KEY in the environment)."""
    import requests

    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise SFLError("YOUTUBE_API_KEY is not set. This step is optional: fill reference.yaml by hand instead.")
    f = REFS / slugify(name) / "reference.yaml"
    doc = load_yaml(f)
    api = "https://www.googleapis.com/youtube/v3"
    ids = [v["video_id"] for v in doc.get("videos") or [] if v.get("video_id")]
    handle = (re.search(r"youtube\.com/@([A-Za-z0-9_.-]+)", doc.get("channel_url") or "") or [None, None])[1]
    if handle and len(ids) < 10:  # add the channel's latest uploads
        r = requests.get(f"{api}/channels", params={"part": "contentDetails", "forHandle": "@" + handle, "key": key},
                         timeout=30)
        _api_ok(r)
        items = r.json().get("items") or []
        if items:
            up = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
            r = requests.get(f"{api}/playlistItems", params={"part": "contentDetails", "playlistId": up,
                                                             "maxResults": 25, "key": key}, timeout=30)
            _api_ok(r)
            for it in r.json().get("items") or []:
                vid = it["contentDetails"]["videoId"]
                if vid not in ids:
                    ids.append(vid)
                    doc.setdefault("videos", []).append({"url": f"https://www.youtube.com/watch?v={vid}", "video_id": vid})
    by = {v.get("video_id"): v for v in doc.get("videos") or []}
    for i in range(0, len(ids), 50):
        r = requests.get(f"{api}/videos", params={"part": "snippet,contentDetails,statistics",
                                                  "id": ",".join(ids[i:i + 50]), "key": key}, timeout=30)
        _api_ok(r)
        for it in r.json().get("items") or []:
            v = by[it["id"]]
            v.update({"title": it["snippet"]["title"], "published": it["snippet"]["publishedAt"][:10],
                      "duration": it["contentDetails"]["duration"],
                      "views": int(it["statistics"].get("viewCount", 0)),
                      "description": it["snippet"].get("description", "")})
    doc["method"] = "youtube_data_api"
    doc["collected_on"] = today()
    save_yaml(f, doc)
    log.info(f"Fetched metadata for {len(ids)} video(s) via the YouTube Data API")


def _api_ok(r):
    if r.status_code != 200:
        raise SFLError(f"YouTube API error {r.status_code}: {r.text[:300]}")


# ---------------------------------------------------------------------------- analysis helpers
def read_transcript(path: Path):
    """Returns (text, [(seconds, text)] if the transcript has timestamps)."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    timed, buf, t = [], [], None
    for line in raw.splitlines():
        line = line.strip()
        m = re.fullmatch(r"(\d{1,2}:\d{2}(?::\d{2})?)", line)
        m2 = re.match(r"^(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)$", line)
        if m:
            t = parse_duration(m.group(1))
            continue
        if m2:
            t, line = parse_duration(m2.group(1)), m2.group(2)
        if line:
            buf.append(line)
            if t is not None:
                timed.append((t, line))
    return " ".join(buf), timed


def measure_video(path: Path, log=None):
    """Cuts per minute, shot length, brightness, saturation - measured from a local file."""
    info = probe(path)
    dur = info["duration"] or 0
    p = subprocess.run([find_tool("ffmpeg"), "-hide_banner", "-nostats", "-i", str(path), "-an", "-vf",
                        "scale=320:-2,scdet=threshold=12,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG,"
                        "metadata=mode=print:key=lavfi.signalstats.SATAVG", "-f", "null", "-"],
                       capture_output=True, text=True)
    cuts = len(re.findall(r"lavfi\.scd\.time", p.stderr))
    yavg = [float(x) for x in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", p.stdout + p.stderr)]
    sat = [float(x) for x in re.findall(r"lavfi\.signalstats\.SATAVG=([\d.]+)", p.stdout + p.stderr)]
    return {"file": rel(path), "seconds": round(dur, 1), "cuts": cuts,
            "cuts_per_minute": round(cuts / (dur / 60), 1) if dur else None,
            "avg_shot_seconds": round(dur / (cuts + 1), 2) if dur else None,
            "brightness_0_255": round(stats.mean(yavg), 1) if yavg else None,
            "saturation_avg": round(stats.mean(sat), 1) if sat else None,
            "resolution": f"{info['width']}x{info['height']}"}


# ---------------------------------------------------------------------------- report
def analyze(name: str, log, video_files=()):
    d = REFS / slugify(name)
    doc = load_yaml(d / "reference.yaml")
    vids = [v for v in doc.get("videos") or [] if v.get("title")]
    L = [f"# Reference analysis — {doc.get('name')}", "",
         f"Channel: {doc.get('channel_url') or '—'} · Data collected: {doc.get('collected_on')} via "
         f"**{doc.get('method')}** · Report: {today()}", "",
         "> Inspiration only. Smart Finds Lab never copies another channel's script, footage, thumbnails or music. "
         "`check-script` automatically flags any 7-word phrase that matches these transcripts.", "",
         "Legend: 📊 based on metadata · 📝 based on transcripts · 🎞️ measured from a local video file · "
         "👁️ needs manual visual review", ""]
    result = {"videos": len(vids)}
    if not vids:
        L += ["⚠️ No video titles in reference.yaml yet - fill them in (or use reference-fetch with an API key).", ""]
    else:
        titles = [v["title"] for v in vids]
        n = len(titles)
        pct = lambda k: f"{100 * k / n:.0f}%"
        has_num = sum(bool(re.search(r"\d", t)) for t in titles)
        starts_num = sum(bool(re.match(r"\s*\d", t)) for t in titles)
        q = sum("?" in t for t in titles)
        ex = sum("!" in t for t in titles)
        par = sum(bool(re.search(r"[()\[\]]", t)) for t in titles)
        yr = sum(bool(re.search(r"\b20\d\d\b", t)) for t in titles)
        caps = sum(bool(re.search(r"\b[A-Z]{3,}\b", t)) for t in titles)
        wordsc = Counter(w for t in titles for w in re.findall(r"[a-z']+", t.lower()) if w not in STOP and len(w) > 2)
        power = Counter(w for t in titles for w in POWER if re.search(rf"\b{w}\b", t.lower()))
        L += [f"## 📊 Titles ({n} videos)", "",
              f"- Average length: **{stats.mean(len(t) for t in titles):.0f} characters**, "
              f"{stats.mean(len(t.split()) for t in titles):.1f} words",
              f"- Contain a number: **{pct(has_num)}** · start with a number: {pct(starts_num)}",
              f"- Questions: {pct(q)} · exclamation marks: {pct(ex)} · brackets/parentheses: {pct(par)} · "
              f"year in title: {pct(yr)} · ALL-CAPS word: {pct(caps)}",
              f"- Most used words: {', '.join(f'{w} ({c})' for w, c in wordsc.most_common(12))}",
              f"- 'Power' words: {', '.join(f'{w} ({c})' for w, c in power.most_common(8)) or 'none'}", ""]
        result["title_avg_chars"] = round(stats.mean(len(t) for t in titles), 1)
        durs = [parse_duration(v.get("duration")) for v in vids if v.get("duration")]
        if durs:
            longf = [x for x in durs if x > 180]
            L += [f"## 📊 Video length ({len(durs)} videos with a duration)", "",
                  f"- Shortest {min(durs) / 60:.1f} min · median **{stats.median(durs) / 60:.1f} min** · "
                  f"longest {max(durs) / 60:.1f} min",
                  f"- Long-form (>3 min): {len(longf)} · Shorts (≤3 min): {len(durs) - len(longf)}", ""]
            result["median_minutes"] = round(stats.median(durs) / 60, 1)
        dates = sorted(dt.date.fromisoformat(str(v["published"])[:10]) for v in vids if v.get("published"))
        if len(dates) >= 3:
            gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
            L += ["## 📊 Upload rhythm", "", f"- {len(dates)} dated videos from {dates[0]} to {dates[-1]}; "
                  f"median gap **{stats.median(gaps):.0f} days** between uploads", ""]
        views = [(v.get("views"), v) for v in vids if isinstance(v.get("views"), (int, float))]
        if views:
            vs = sorted(views, key=lambda x: -x[0])
            L += ["## 📊 Views", "", f"- Median views: **{stats.median([x for x, _ in views]):,.0f}**",
                  "- Best performers: " + "; ".join(f"\"{v['title']}\" ({x:,.0f})" for x, v in vs[:3]), ""]
        chs = [(v, chapters_from_description(v.get("description"))) for v in vids]
        chs = [(v, c) for v, c in chs if c]
        if chs:
            first = [c[1][0] for _, c in chs if len(c) > 1]
            seg = [b[0] - a[0] for _, c in chs for a, b in zip(c, c[1:])]
            names = Counter(re.sub(r"\d+", "#", c_[1]).strip() for _, c in chs for c_ in c)
            L += [f"## 📊 Structure from chapters ({len(chs)} videos with chapters)", "",
                  f"- Chapters per video: {stats.mean(len(c) for _, c in chs):.1f}",
                  f"- Intro (first chapter) length: median **{stats.median(first):.0f} s**" if first else "",
                  f"- Average chapter length: **{stats.mean(seg):.0f} s**" if seg else "",
                  f"- Chapter name patterns: {', '.join(f'{k} ({c})' for k, c in names.most_common(6))}", ""]
            result["chapters_videos"] = len(chs)
    # ---- transcripts
    tfiles = sorted((d / "transcripts").glob("*.txt"))
    if tfiles:
        dur_by = {v.get("video_id"): parse_duration(v.get("duration")) for v in doc.get("videos") or []}
        rows, hooks, sent_len, you, cta_pos, grams = [], [], [], [], [], Counter()
        for f in tfiles:
            text, timed = read_transcript(f)
            w = re.findall(r"[A-Za-z0-9']+", text)
            dur = dur_by.get(f.stem) or (timed[-1][0] if timed else None)
            wpm = len(w) / (dur / 60) if dur else None
            sents = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
            sent_len += [len(s.split()) for s in sents]
            you.append(sum(1 for x in w if x.lower() in ("you", "your", "you're")) / max(1, len(w)))
            hook = " ".join(w[:45])
            hooks.append((f.stem, hook, "?" in " ".join(sents[:2])))
            low = text.lower()
            first_cta = min([low.find(c) for c in CTA_WORDS if c in low] or [-1])
            if first_cta >= 0:
                cta_pos.append(first_cta / max(1, len(low)))
            ww = [x.lower() for x in w]
            grams.update(" ".join(ww[i:i + 3]) for i in range(len(ww) - 2))
            rows.append((f.stem, len(w), wpm))
        L += [f"## 📝 Narration ({len(tfiles)} transcripts)", "",
              "| Video | Words | Words/min |", "|---|---|---|"] + \
             [f"| {a} | {b:,} | {c:.0f} |" if c else f"| {a} | {b:,} | — |" for a, b, c in rows] + [""]
        wpms = [c for _, _, c in rows if c]
        L += [f"- Speaking pace: **{stats.mean(wpms):.0f} words/min**" if wpms else "- Speaking pace: needs durations",
              f"- Average sentence: {stats.mean(sent_len):.1f} words",
              f"- Talks to the viewer ('you'): {100 * stats.mean(you):.1f}% of words",
              f"- First call-to-action appears at ~{100 * stats.median(cta_pos):.0f}% of the transcript" if cta_pos
              else "- No subscribe/comment call-to-action found", "",
              "### 📝 Hooks (first words, shortened — for pattern study only, do not reuse)", ""]
        L += [f"- `{vid}`: {' '.join(h.split()[:12])}… {'(opens with a question)' if qm else ''}" for vid, h, qm in hooks]
        common = [g for g, c in grams.most_common(40) if c >= 3 and not set(g.split()) <= STOP][:10]
        if common:
            L += ["", "Signature phrases (repeated 3+ times) — **avoid these in our scripts**: " + ", ".join(
                f"\"{g}\"" for g in common)]
        L.append("")
        result["transcripts"] = len(tfiles)
        result["wpm"] = round(stats.mean(wpms)) if wpms else None
    else:
        L += ["## 📝 Narration", "", "No transcripts yet. Hook, pacing (words/min) and narration style need "
              f"transcripts in `{rel(d / 'transcripts')}/`.", ""]
    # ---- local video measurements
    if video_files:
        ms = [measure_video(Path(v), log) for v in video_files]
        L += ["## 🎞️ Measured from local video files", "",
              "| File | Length | Cuts | Cuts/min | Avg shot | Brightness | Saturation |", "|---|---|---|---|---|---|---|"]
        L += [f"| {m['file']} | {m['seconds']}s | {m['cuts']} | {m['cuts_per_minute']} | {m['avg_shot_seconds']}s | "
              f"{m['brightness_0_255']} | {m['saturation_avg']} |" for m in ms]
        L += ["", "*Cut detection is automatic (scene-change threshold); fades and fast motion can add or hide cuts.*", ""]
        result["measured"] = ms
    # ---- manual
    mo = doc.get("manual_observations") or {}
    L += ["## 👁️ Requires manual visual review", "",
          "These cannot be measured from data. Watch 2–3 videos and write notes in `manual_observations` "
          "(reference.yaml):", ""]
    for k in ("visual_style", "on_screen_text", "b_roll_and_footage", "thumbnail_style", "music_and_sound",
              "presenter_or_faceless", "editing_pace_feel"):
        L.append(f"- **{k.replace('_', ' ')}**: {mo.get(k) or '⏳ not reviewed yet'}")
    L += ["", "## What to take into our videos (fill after review)", "",
          "- Structure ideas (not wording):", "- Pacing target (words/min, shot length):", "- Visual ideas:",
          "- What we will do differently:", ""]
    out = d / "report.md"
    out.write_text("\n".join(x for x in L if x is not None) + "\n", encoding="utf-8")
    (d / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log.info(f"Reference report: {rel(out)}")
    return result
