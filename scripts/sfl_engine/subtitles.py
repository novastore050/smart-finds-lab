"""Subtitles: read SRT/VTT, estimate timings from script text, optional Whisper, line splitting."""
from __future__ import annotations

import re
from pathlib import Path

from .util import SFLError, rel

_TIME = r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"


def _t(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def parse_subtitle_file(path: Path):
    """Read .srt or .vtt -> list of (start, end, text)."""
    if not path.exists():
        raise SFLError(f"Subtitle file not found: {rel(path)}")
    text = path.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text):
        lines = [ln for ln in block.strip().split("\n") if ln.strip()]
        for i, ln in enumerate(lines):
            m = re.search(_TIME + r"\s*-->\s*" + _TIME, ln)
            if m:
                g = m.groups()
                body = " ".join(lines[i + 1:])
                body = re.sub(r"<[^>]+>", "", body).strip()
                if body:
                    cues.append((_t(*g[:4]), _t(*g[4:]), body))
                break
    if not cues:
        raise SFLError(f"No subtitles could be read from {rel(path)} - is it a valid .srt file?")
    return sorted(cues)


def fmt_srt_time(t: float) -> str:
    t = max(0.0, t)
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues, path: Path):
    lines = []
    for i, (a, b, txt) in enumerate(cues, 1):
        lines += [str(i), f"{fmt_srt_time(a)} --> {fmt_srt_time(b)}", txt.replace("\\N", "\n"), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- script timing
def split_sentences(text: str):
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def script_to_cues(text: str, t0: float, t1: float, max_chars: int = 84):
    """Spread script text evenly (by character count) over [t0, t1]. Timing is an ESTIMATE."""
    pieces = []
    for sent in split_sentences(text):
        pieces += split_text(sent, max_chars)
    if not pieces or t1 <= t0:
        return []
    weights = [len(p) + 8 for p in pieces]  # +8: small pause per piece
    total = sum(weights)
    cues, t = [], t0
    for p, w in zip(pieces, weights):
        d = (t1 - t0) * w / total
        cues.append((t, t + d, p))
        t += d
    return cues


def split_text(text: str, max_chars: int):
    """Split a sentence into pieces no longer than max_chars, preferring commas/word breaks."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    # try a comma/semicolon/dash near the middle first
    best = None
    for m in re.finditer(r"[,;:—-]\s", text):
        pos = m.end()
        if 0.3 * len(text) <= pos <= 0.7 * len(text) and pos <= max_chars + 5:
            if best is None or abs(pos - len(text) / 2) < abs(best - len(text) / 2):
                best = pos
    if best is None:
        words, cur, out = text.split(), "", []
        target = len(text) / max(2, -(-len(text) // max_chars))
        for w in words:
            if cur and len(cur) + 1 + len(w) > min(max_chars, target + 10):
                out.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        if cur:
            out.append(cur)
        res = []
        for o in out:
            res += split_text(o, max_chars) if len(o) > max_chars and " " in o else [o]
        return res
    return split_text(text[:best], max_chars) + split_text(text[best:], max_chars)


def wrap_two_lines(text: str, max_line: int) -> str:
    """Balance a cue over 1-2 lines for long-form subtitles (ASS line break = \\N)."""
    if len(text) <= max_line:
        return text
    words = text.split()
    best, best_score = text, 10**9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = max(len(a), len(b))
        if score < best_score:
            best, best_score = f"{a}\\N{b}", score
    return best


def chunk_for_display(cues, max_chars: int, max_words: int | None = None):
    """Split cues into smaller timed chunks (proportional to length)."""
    out = []
    for a, b, txt in cues:
        if max_words:
            words, chunks, cur = txt.split(), [], []
            for w in words:
                trial = " ".join(cur + [w])
                if cur and (len(cur) >= max_words or len(trial) > max_chars):
                    chunks.append(" ".join(cur))
                    cur = [w]
                else:
                    cur.append(w)
                # end chunk after punctuation for natural phrasing
                if cur and re.search(r"[.!?,;:]$", w):
                    chunks.append(" ".join(cur))
                    cur = []
            if cur:
                chunks.append(" ".join(cur))
        else:
            chunks = split_text(txt, max_chars)
        if not chunks:
            continue
        weights = [len(c) + 3 for c in chunks]
        tot, t = sum(weights), a
        for c, w in zip(chunks, weights):
            d = (b - a) * w / tot
            out.append((t, t + d, c))
            t += d
    return out


# --------------------------------------------------------------------------- whisper (optional)
def whisper_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def whisper_cues(audio: Path, log=None, model_size: str = "small.en"):
    """Transcribe with faster-whisper (optional install). Returns cues with real word timings."""
    from faster_whisper import WhisperModel  # type: ignore

    if log:
        log.info(f"    transcribing {rel(audio)} with Whisper ({model_size}) ...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio), word_timestamps=True, vad_filter=True)
    cues = []
    for seg in segments:
        words = list(seg.words or [])
        if not words:
            cues.append((seg.start, seg.end, seg.text.strip()))
            continue
        cur, start = [], None
        for w in words:
            if start is None:
                start = w.start
            cur.append(w.word.strip())
            if len(" ".join(cur)) > 70 or re.search(r"[.!?]$", w.word.strip()):
                cues.append((start, w.end, " ".join(cur)))
                cur, start = [], None
        if cur:
            cues.append((start, words[-1].end, " ".join(cur)))
    return cues
