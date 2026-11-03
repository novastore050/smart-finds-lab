"""Voice-over: one consistent ElevenLabs voice, per-scene text export, import, word-level subtitles.

Three ways to get the audio (all use the SAME voice/model/settings from config/voice.yaml):
  A) ElevenLabs website: paste each scene's text file, download MP3s -> import-voice   (manual, works today)
  B) Claude + ElevenLabs connector: Claude reads voice/voice-jobs.json and generates each scene
     (spends ElevenLabs credits -> only after the owner approves the estimate)
  C) Direct API: studio.py tts --confirm-spend   (needs ELEVENLABS_API_KEY in the environment and
     network access to api.elevenlabs.io; refuses to run without --confirm-spend)

Word-level subtitles: any word-timing JSON next to the audio (ElevenLabs transcription 'words',
ElevenLabs TTS 'alignment', or Whisper) is converted to voice/<scene>.srt. The editing timeline then
uses that SRT, so subtitles match the real voice exactly.
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from sfl_engine.subtitles import write_srt
from sfl_engine.util import AUDIO_EXT, ROOT, SFLError, probe, rel

from .common import Production, load_yaml, save_yaml
from .script import est_seconds, load_script, voice_units

API = "https://api.elevenlabs.io"


def voice_cfg() -> dict:
    return load_yaml(ROOT / "config" / "voice.yaml")


def speakable(text: str, cfg: dict) -> str:
    """Text as sent to the voice: pronunciation fixes applied (subtitles keep the original)."""
    out = text
    for word, say in (cfg.get("pronunciations") or {}).items():
        if word != say:
            out = re.sub(rf"\b{re.escape(word)}\b", say, out)
    return re.sub(r"\s+", " ", out).strip()


def text_md5(text: str) -> str:
    import hashlib
    return hashlib.md5(" ".join(str(text).split()).encode("utf-8")).hexdigest()


def stamp_voice(prod: Production, sid: str, narration: str):
    """Remember which narration text a voice file was made from (to catch stale audio later)."""
    prod.p("voice", f"{sid}.text-md5").write_text(text_md5(narration) + "\n", encoding="utf-8")


def stale_voice(prod: Production, units: list) -> list:
    """Voice files whose recorded text no longer matches the script (or that have no record)."""
    out = []
    for u in units:
        if not scene_audio(prod, u["id"]):
            continue
        rec = prod.p("voice", f"{u['id']}.text-md5")
        if not rec.exists() or rec.read_text().strip() != text_md5(u.get("narration", "")):
            out.append(u["id"])
    return out


def scene_audio(prod: Production, sid: str):
    for e in sorted(AUDIO_EXT):
        f = prod.p("voice", f"{sid}{e}")
        if f.exists():
            return f
    return None


# ---------------------------------------------------------------------------- export
def export_pack(prod: Production, log):
    prod.require("script", why="Write and check the script first.")
    cfg = voice_cfg()
    s = load_script(prod)
    wpm = float(s.get("words_per_minute") or 155)
    tdir = prod.p("voice", "text")
    tdir.mkdir(parents=True, exist_ok=True)
    jobs, total_chars = [], 0
    for sc in voice_units(s):
        text = speakable(sc.get("narration", ""), cfg)
        (tdir / f"{sc['id']}.txt").write_text(text + "\n", encoding="utf-8")
        total_chars += len(text)
        jobs.append({"scene": sc["id"], "text": text, "chars": len(text),
                     "est_seconds": est_seconds(sc.get("narration", ""), wpm),
                     "save_audio_as": rel(prod.p("voice", f"{sc['id']}.mp3")),
                     "save_word_timings_as": rel(prod.p("voice", f"{sc['id']}.words.json")),
                     "kind": sc["kind"],
                     "status": "imported" if scene_audio(prod, sc["id"]) else "pending"})
    pack = {"voice_name": cfg["voice"]["name"], "voice_id": cfg["voice"]["voice_id"], "model_id": cfg["model_id"],
            "output_format": cfg.get("output_format"), "voice_settings": cfg.get("voice_settings"),
            "total_characters": total_chars,
            "credit_note": "ElevenLabs bills by characters. On most models about 1 credit per character "
                           "(Flash/Turbo about 0.5). Check the exact cost with an estimate before generating.",
            "jobs": jobs}
    prod.p("voice", "voice-jobs.json").write_text(json.dumps(pack, indent=2), encoding="utf-8")
    L = [f"# Voice-over pack — {prod.title}", "",
         f"Voice: **{cfg['voice']['name']}** (`{cfg['voice']['voice_id']}`) · model `{cfg['model_id']}` · "
         f"total **{total_chars:,} characters** (~{total_chars:,} credits on standard models — estimate only).", "",
         "**Nothing has been generated.** Choose one way:", "",
         "**A) ElevenLabs website (manual):** open Text to Speech, pick the voice above, set the same settings "
         f"({', '.join(f'{k}={v}' for k, v in (cfg.get('voice_settings') or {}).items())}), paste each file from "
         "`voice/text/`, download as MP3 named after the scene (`s01.mp3` …), then run:", "",
         f"```bash\npython scripts/studio.py import-voice {prod.slug} \"PATH/TO/DOWNLOADS\"\n```", "",
         "**B) Ask Claude** (ElevenLabs connector) to generate the jobs in `voice/voice-jobs.json` — Claude must show "
         "you the credit estimate and get your OK first.", "",
         "**C) Direct API** — see docs/VOICE-ELEVENLABS.md (needs your own API key in the environment).", "",
         "| Scene | Characters | ~Seconds | Status |", "|---|---|---|---|"]
    L += [f"| {j['scene']} | {j['chars']} | {j['est_seconds']} | {'✅ ' if j['status'] == 'imported' else '⏳ '}{j['status']} |"
          for j in jobs]
    prod.p("voice", "README.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    log.info(f"Voice pack: {rel(prod.p('voice', 'voice-jobs.json'))} ({len(jobs)} scenes, {total_chars:,} characters)")
    return pack


# ---------------------------------------------------------------------------- import
SCENE_RE = re.compile(r"(?<![a-z0-9])(s\d{2}|short\d+)(?![0-9])", re.I)


def import_voice(prod: Production, folder, log):
    src = Path(folder).expanduser()
    if not src.is_dir():
        raise SFLError(f"Folder not found: {src}")
    s = load_script(prod)
    scenes = {sc["id"]: sc for sc in voice_units(s)}
    wpm = float(s.get("words_per_minute") or 155)
    n = 0
    for f in sorted(src.iterdir()):
        m = SCENE_RE.search(f.stem)
        if not m or m.group(1).lower() not in scenes:
            if f.suffix.lower() in AUDIO_EXT:
                log.info(f"   skipped {f.name} (no scene id like s03 or short1 in the name)")
            continue
        sid = m.group(1).lower()
        ext = f.suffix.lower()
        if ext in AUDIO_EXT:
            dest = prod.p("voice", f"{sid}{ext}")
        elif ext == ".json":
            dest = prod.p("voice", f"{sid}.words.json")
        elif ext in (".srt", ".vtt"):
            dest = prod.p("voice", f"{sid}{ext}")
        else:
            continue
        if dest.exists():
            log.warn(f"{rel(dest)} already exists - not replaced (delete it first to re-import)")
            continue
        shutil.copy2(f, dest)
        if ext in AUDIO_EXT:
            stamp_voice(prod, sid, scenes[sid].get("narration", ""))
        n += 1
        msg = ""
        if ext in AUDIO_EXT:
            info = probe(dest)
            est = est_seconds(scenes[sid].get("narration", ""), wpm)
            dur = info.get("audio_duration") or info.get("duration") or 0
            if est and not (0.6 * est <= dur <= 1.6 * est):
                msg = f"  WARNING: {dur:.1f}s but the script suggests ~{est:.0f}s - is it the right scene?"
            else:
                msg = f"  {dur:.1f}s"
        log.info(f"   {f.name} -> {rel(dest)}{msg}")
    log.info(f"Imported {n} file(s); originals untouched.")
    missing = [sid for sid in scenes if not scene_audio(prod, sid)]
    if missing:
        log.info(f"Still missing voice for: {', '.join(missing)}")
    return n


# ---------------------------------------------------------------------------- word timings -> SRT
def parse_word_timings(data) -> list:
    """Normalise ElevenLabs / Whisper timing JSON to [(word, start, end)]."""
    if isinstance(data, dict) and "alignment" in data:
        data = data["alignment"]
    if isinstance(data, dict) and "characters" in data:  # ElevenLabs TTS with-timestamps
        chars = data["characters"]
        st, en = data["character_start_times_seconds"], data["character_end_times_seconds"]
        out, cur, a, b = [], "", None, None
        for c, s0, e0 in zip(chars, st, en):
            if c.isspace():
                if cur:
                    out.append((cur, a, b))
                cur, a = "", None
                continue
            if a is None:
                a = s0
            cur += c
            b = e0
        if cur:
            out.append((cur, a, b))
        return out
    if isinstance(data, dict):
        for k in ("words", "transcripts", "segments"):
            if k in data:
                data = data[k]
                break
    if isinstance(data, list) and data and isinstance(data[0], dict) and "words" in data[0]:
        data = [w for seg in data for w in seg["words"]]  # list of transcripts/segments
    out = []
    for w in data or []:
        if not isinstance(w, dict):
            continue
        if w.get("type") in ("spacing", "audio_event"):
            continue
        t = str(w.get("text", w.get("word", ""))).strip()
        if t and w.get("start") is not None and w.get("end") is not None:
            out.append((t, float(w["start"]), float(w["end"])))
    return out


def words_to_cues(words, max_chars=80, max_dur=6.0, min_gap=0.35):
    cues, cur, a, b = [], [], None, None
    for t, s0, e0 in words:
        if cur and (len(" ".join(cur + [t])) > max_chars or e0 - a > max_dur or s0 - b > min_gap * 3):
            cues.append((a, b, " ".join(cur)))
            cur, a = [], None
        if a is None:
            a = s0
        cur.append(t)
        b = e0
        if re.search(r"[.!?]$", t):
            cues.append((a, b, " ".join(cur)))
            cur, a = [], None
    if cur:
        cues.append((a, b, " ".join(cur)))
    return cues


def align(prod: Production, log):
    """Turn every voice/<scene>.words.json into voice/<scene>.srt (exact word timing)."""
    s = load_script(prod)
    made = 0
    for sc in voice_units(s):
        j = prod.p("voice", f"{sc['id']}.words.json")
        if not j.exists():
            continue
        words = parse_word_timings(json.loads(j.read_text(encoding="utf-8")))
        if not words:
            log.warn(f"{rel(j)} contains no word timings")
            continue
        out = prod.p("voice", f"{sc['id']}.srt")
        write_srt(words_to_cues(words), out)
        made += 1
        log.info(f"   {rel(out)}  ({len(words)} words)")
    log.info(f"{made} subtitle file(s) created from word timings.")
    return made


# ---------------------------------------------------------------------------- previews (free)
def download_samples(log):
    """Download the FREE public preview clips of the candidate voices (no credits used)."""
    cfg = voice_cfg()
    out = ROOT / "productions" / "_voice-samples"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cfg.get("candidates") or []:
        name = re.sub(r"[^a-z0-9]+", "-", c["name"].split(" - ")[0].lower()).strip("-")
        dest = out / f"{name}-preview.mp3"
        if not dest.exists():
            r = subprocess.run(["curl", "-sSfL", "--max-time", "30", "-o", str(dest), c["preview_url"]],
                               capture_output=True, text=True)
            if r.returncode != 0:
                log.warn(f"could not download {c['name']} preview: {r.stderr.strip()[:200]}")
                continue
        info = probe(dest)
        rows.append((c, dest, info.get("audio_duration") or info.get("duration")))
        log.info(f"   {c['name']}: {rel(dest)} ({rows[-1][2]:.1f}s)")
    L = ["# Voice comparison (free ElevenLabs library previews)", "",
         "Each preview is the voice owner's own demo text, so compare **tone, clarity and energy**, not the words.",
         "Listen on headphones and on a phone speaker. Pick one voice and keep it for every video.", "",
         "| Voice | Description | Preview | Length |", "|---|---|---|---|"]
    L += [f"| {c['name']} (`{c['voice_id']}`) | {c['description']} | `{rel(d)}` | {dur:.1f}s |" for c, d, dur in rows]
    L += ["", "To choose: edit `config/voice.yaml` → set `voice:` to the chosen candidate and `status: chosen`.",
          "", "Previews are ElevenLabs' files: keep them for listening only (they are not committed to GitHub)."]
    (out / "COMPARISON.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return rows


# ---------------------------------------------------------------------------- direct API (optional)
def api_request(text: str, cfg: dict) -> dict:
    """Build (not send) the ElevenLabs TTS-with-timestamps request. Pure function, testable offline."""
    url = f"{API}/v1/text-to-speech/{cfg['voice']['voice_id']}/with-timestamps"
    if cfg.get("output_format"):
        url += f"?output_format={cfg['output_format']}"
    body = {"text": text, "model_id": cfg["model_id"], "voice_settings": cfg.get("voice_settings") or {}}
    return {"url": url, "json": body}


def save_api_response(resp: dict, audio_path: Path, words_path: Path):
    audio_path.write_bytes(base64.b64decode(resp["audio_base64"]))
    if resp.get("alignment"):
        words_path.write_text(json.dumps({"alignment": resp["alignment"]}), encoding="utf-8")


def tts_api(prod: Production, log, scenes=None, confirm_spend=False):
    """Generate voice-over through the ElevenLabs API. Spends credits -> needs confirm_spend=True.
    NOTE: not live-tested from the build environment (API host blocked, no key, credits)."""
    import requests

    cfg = voice_cfg()
    pack = export_pack(prod, log)
    jobs = [j for j in pack["jobs"] if (not scenes or j["scene"] in scenes) and j["status"] != "imported"]
    chars = sum(j["chars"] for j in jobs)
    log.info(f"{len(jobs)} scene(s), {chars:,} characters to generate with {cfg['voice']['name']}.")
    if not confirm_spend:
        log.info("DRY RUN - nothing sent. Add --confirm-spend to generate (this uses ElevenLabs credits).")
        return []
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise SFLError("ELEVENLABS_API_KEY is not set in the environment (never put it in a file).")
    done = []
    for j in jobs:
        req = api_request(j["text"], cfg)
        r = requests.post(req["url"], json=req["json"], headers={"xi-api-key": key}, timeout=180)
        if r.status_code != 200:
            raise SFLError(f"ElevenLabs API error {r.status_code} for {j['scene']}: {r.text[:300]}")
        save_api_response(r.json(), prod.p("voice", f"{j['scene']}.mp3"), prod.p("voice", f"{j['scene']}.words.json"))
        unit = next((u for u in voice_units(load_script(prod)) if u["id"] == j["scene"]), {})
        stamp_voice(prod, j["scene"], unit.get("narration", ""))
        done.append(j["scene"])
        log.info(f"   {j['scene']}: saved")
    align(prod, log)
    return done
