"""Motion graphics + subtitles, written as one Advanced SubStation (.ass) file.

FFmpeg's 'ass' filter (libass) burns this file onto the video. Using ASS gives us
smooth animation (pop-in, wipe reveal, slide, fade), rounded boxes and exact fonts,
all controlled by config/brand.yaml.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

from .plan import Plan
from .subtitles import chunk_for_display, wrap_two_lines
from .util import ROOT, SFLError, ass_color, ass_color_tag, resolve


def _ts(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(text: str) -> str:
    """Make user text safe for ASS (keeps our own \\N line breaks)."""
    s = str(text).replace("\\N", "\x00").replace("\\", "/").replace("{", "(").replace("}", ")")
    return s.replace("\n", "\x00").replace("\x00", "\\N")


def rrect(w, h, r):
    """ASS vector drawing of a rounded rectangle with top-left at (0,0)."""
    w, h = round(w), round(h)
    r = max(0, min(r, w / 2, h / 2))
    k = 0.4477 * r  # control-point distance for a circular arc
    return (f"m {r:.0f} 0 l {w - r:.0f} 0 b {w - r + k:.0f} 0 {w:.0f} {r - k:.0f} {w:.0f} {r:.0f} "
            f"l {w:.0f} {h - r:.0f} b {w:.0f} {h - r + k:.0f} {w - r + k:.0f} {h:.0f} {w - r:.0f} {h:.0f} "
            f"l {r:.0f} {h:.0f} b {r - k:.0f} {h:.0f} 0 {h - r + k:.0f} 0 {h - r:.0f} "
            f"l 0 {r:.0f} b 0 {r - k:.0f} {r - k:.0f} 0 {r:.0f} 0")


class Graphics:
    def __init__(self, plan: Plan):
        self.plan = plan
        self.p = plan.project
        self.W, self.H = plan.W, plan.H
        self.b = self.p.brand
        self.fmt = self.p.fmt
        self.sz = self.b["text_sizes"][self.fmt]
        self.col = self.b["colors"]
        self.u = min(self.W, self.H) / 1080
        self.events = []
        self._fonts = {}
        fonts = self.b["fonts"]
        self.font_dir = resolve(fonts.get("folder", "assets/fonts"))
        self.font_name = {k: fonts[k]["name"] for k in ("heading", "body", "caption")}
        for k in ("heading", "body", "caption"):
            f = self.font_dir / fonts[k]["file"]
            if not f.exists():
                raise SFLError(f"Font file missing: {f}. Check 'fonts' in config/brand.yaml")
        # safe margins (shorts keep clear of YouTube's buttons and title area)
        if self.fmt == "long":
            self.m = {"l": 90 * self.u, "r": 90 * self.u, "t": 70 * self.u, "b": 190 * self.u}
        else:
            self.m = {"l": 70 * self.u, "r": 150 * self.u, "t": 0.11 * self.H, "b": 0.26 * self.H}

    # ------------------------------------------------------------------ measuring
    def font(self, key, size):
        fk = (key, round(size, 1))
        if fk not in self._fonts:
            path = str(self.font_dir / self.b["fonts"][key]["file"])
            probe = ImageFont.truetype(path, 100)
            a, d = probe.getmetrics()
            self._fonts[fk] = ImageFont.truetype(path, max(1, size * 100 / (a + d)))
        return self._fonts[fk]

    def width(self, key, size, text):
        return self.font(key, size).getlength(str(text)) * 1.02 + 2

    def wrap(self, key, size, text, max_w):
        """Greedy wrap into lines that fit max_w pixels."""
        words, lines, cur = str(text).split(), [], ""
        for w in words:
            trial = f"{cur} {w}".strip()
            if cur and self.width(key, size, trial) > max_w:
                lines.append(cur)
                cur = w
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return lines or [""]

    # ------------------------------------------------------------------ events
    def add(self, t0, t1, text, layer=0, style="Base"):
        if t1 - t0 > 0.02:
            self.events.append((layer, t0, t1, style, text))

    def draw(self, t0, t1, x, y, w, h, r, color, alpha=0.0, extra="", layer=1, an=7):
        tag = (f"{{\\an{an}\\pos({x:.0f},{y:.0f})\\bord0\\shad0\\1c{ass_color_tag(color)}"
               f"\\1a&H{int(alpha * 255):02X}&{extra}\\p1}}")
        self.add(t0, t1, tag + rrect(w, h, r) + "{\\p0}", layer, "Shape")

    def txt(self, t0, t1, x, y, text, font, size, color, an=7, extra="", layer=2, alpha=0.0):
        tag = (f"{{\\an{an}\\pos({x:.0f},{y:.0f})\\fn{self.font_name[font]}\\fs{size:.0f}"
               f"\\1c{ass_color_tag(color)}\\1a&H{int(alpha * 255):02X}&{extra}}}")
        self.add(t0, t1, tag + _esc(text), layer)

    def anchor(self, pos, w, h, default):
        """Top-left corner for a box of size w x h at a named position (or {x:,y:})."""
        pos = pos or default
        if isinstance(pos, dict):
            return float(pos.get("x", 0)), float(pos.get("y", 0))
        if isinstance(pos, (list, tuple)):
            return float(pos[0]), float(pos[1])
        m, W, H = self.m, self.W, self.H
        pos = str(pos).replace("_", "-")
        x = {"left": m["l"], "right": W - m["r"] - w}.get(next((p for p in ("left", "right") if p in pos), ""),
                                                           (W - w) / 2)
        if pos.startswith("top"):
            y = m["t"]
        elif pos.startswith("bottom"):
            y = H - m["b"] - h
        elif pos in ("left", "right"):
            y = H * 0.30
        else:
            y = (H - h) / 2
        return x, y

    # ------------------------------------------------------------------ overlay types
    def lower_third(self, t0, t1, d):
        u = self.u
        main, sub = str(d.get("text", "")), str(d.get("subtitle", "") or "")
        fs, fs2 = self.sz["lower_third"], self.sz["lower_third_sub"]
        pad, bar, gap = 26 * u, 10 * u, 22 * u
        tw = self.width("heading", fs, main)
        sw = self.width("body", fs2, sub) if sub else 0
        bw = max(tw, sw) + pad * 2 + bar + gap - pad
        bh = pad * 0.9 + fs * 1.05 + (fs2 * 1.25 if sub else 0) + pad * 0.8
        # Shorts: below the corner badge, clear of the hook and YouTube's buttons
        default = "bottom-left" if self.fmt == "long" else {"x": self.m["l"], "y": 0.20 * self.H}
        x, y = self.anchor(d.get("position"), bw, bh, default)
        dur_in = 450
        clip0 = f"\\clip({x:.0f},{y:.0f},{x + 1:.0f},{y + bh:.0f})"
        clip1 = f"\\clip({x:.0f},{y:.0f},{x + bw:.0f},{y + bh:.0f})"
        anim = f"{clip0}\\t(0,{dur_in},0.5,{clip1})\\fad(0,300)"
        self.draw(t0, t1, x, y, bw, bh, 12 * u, self.col["dark"], 0.12, anim, layer=1)
        self.draw(t0, t1, x, y, bar, bh, 4 * u, self.col["primary"], 0, anim, layer=2)
        tx = x + bar + gap
        self.txt(t0, t1, tx, y + pad * 0.9, main, "heading", fs, self.col["light"], extra=anim, layer=3)
        if sub:
            self.txt(t0, t1, tx, y + pad * 0.9 + fs * 1.12, sub, "body", fs2, self.col["muted"], extra=anim, layer=3)

    def badge(self, t0, t1, d):
        u = self.u
        text = str(d.get("text", ""))
        fs = self.sz["badge"]
        h = fs * 1.55
        w = max(h, self.width("heading", fs, text) + 44 * u)
        x, y = self.anchor(d.get("position"), w, h, "top-left")
        cx, cy = x + w / 2, y + h / 2
        pop = "\\fscx30\\fscy30\\t(0,170,\\fscx112\\fscy112)\\t(170,280,\\fscx100\\fscy100)\\fad(100,250)"
        self.draw(t0, t1, cx, cy, w, h, 18 * u, self.col["primary"], 0, pop, layer=4, an=5)
        self.txt(t0, t1, cx, cy + fs * 0.03, text, "heading", fs, self.col["dark"], an=5, extra=pop, layer=5)

    def callout(self, t0, t1, d):
        u = self.u
        text = str(d.get("text", ""))
        fs = float(d.get("size") or self.sz["callout"])
        padx, pady = 30 * u, 16 * u
        w, h = self.width("heading", fs, text) + padx * 2, fs * 1.1 + pady * 2
        x, y = self.anchor(d.get("position"), w, h, "right")
        dx = 50 * u if x > self.W / 2 else -50 * u
        mv = lambda xx, yy: f"\\move({xx + dx:.0f},{yy:.0f},{xx:.0f},{yy:.0f},0,300)\\fad(220,250)"
        bg = d.get("color") or self.col["secondary"]
        self.add(t0, t1, f"{{\\an7{mv(x, y)}\\bord0\\shad0\\1c{ass_color_tag(bg)}\\p1}}"
                 + rrect(w, h, h / 2) + "{\\p0}", 4, "Shape")
        self.add(t0, t1, f"{{\\an7{mv(x + padx, y + pady)}\\fn{self.font_name['heading']}\\fs{fs:.0f}"
                 f"\\1c{ass_color_tag(d.get('text_color') or self.col['dark'])}}}{_esc(text)}", 5)

    def cta(self, t0, t1, d):
        u = self.u
        text = str(d.get("text") or "Links in the description")
        if d.get("arrow", True) and not text.startswith(("↓", "↑")):
            text = "↓  " + text
        fs = self.sz["cta"]
        padx, pady = 30 * u, 16 * u
        w, h = self.width("heading", fs, text) + padx * 2, fs * 1.1 + pady * 2
        x, y = self.anchor(d.get("position"), w, h, "bottom-right" if self.fmt == "long" else "bottom")
        mv = lambda xx, yy: f"\\move({xx:.0f},{yy + 40 * u:.0f},{xx:.0f},{yy:.0f},0,300)\\fad(220,250)"
        self.add(t0, t1, f"{{\\an7{mv(x, y)}\\bord0\\shad0\\1c{ass_color_tag(self.col['primary'])}\\p1}}"
                 + rrect(w, h, h / 2) + "{\\p0}", 4, "Shape")
        self.add(t0, t1, f"{{\\an7{mv(x + padx, y + pady)}\\fn{self.font_name['heading']}\\fs{fs:.0f}"
                 f"\\1c{ass_color_tag(self.col['dark'])}}}{_esc(text)}", 5)

    def title(self, t0, t1, d):
        u = self.u
        fs = float(d.get("size") or self.sz["title"])
        lines = self.wrap("heading", fs, d.get("text", ""), self.W * 0.84)
        sub = str(d.get("subtitle", "") or "")
        fs2 = self.sz["card_sub"]
        block_h = fs * 1.1 * len(lines) + (fs2 * 1.6 if sub else 0) + 30 * u
        tw = max(self.width("heading", fs, ln) for ln in lines)
        x, y = self.anchor(d.get("position"), tw, block_h, "center")
        cx = x + tw / 2
        soft = "\\bord2\\3c&H000000&\\3a&H90&\\shad3\\4a&H70&\\blur3"
        pop = "\\fscx85\\fscy85\\t(0,220,0.6,\\fscx100\\fscy100)\\fad(180,260)"
        self.txt(t0, t1, cx, y, "\\N".join(lines), "heading", fs, d.get("color") or self.col["light"],
                 an=8, extra=pop + soft, layer=5)
        ly = y + fs * 1.1 * len(lines) + 12 * u
        bar_w = min(tw * 0.35, 220 * u)
        self.draw(t0, t1, cx, ly, bar_w, 8 * u, 4 * u, self.col["primary"], 0,
                  "\\fscx0\\t(150,520,0.5,\\fscx100)\\fad(0,260)", layer=5, an=8)
        if sub:
            self.txt(t0, t1, cx, ly + 26 * u, sub, "body", fs2, self.col["light"], an=8,
                     extra="\\alpha&HFF&\\t(250,550,\\alpha&H00&)\\fad(0,260)" + soft, layer=5)

    def text(self, t0, t1, d):
        fs = float(d.get("size") or self.sz["callout"])
        font = d.get("font", "heading")
        lines = self.wrap(font, fs, d.get("text", ""), self.W * 0.84)
        tw = max(self.width(font, fs, ln) for ln in lines)
        th = fs * 1.15 * len(lines)
        x, y = self.anchor(d.get("position"), tw, th, "center")
        soft = "\\bord2\\3c&H000000&\\3a&H80&\\shad2\\4a&H70&\\blur2"
        if d.get("box"):
            pad = 20 * self.u
            self.draw(t0, t1, x - pad, y - pad * 0.7, tw + pad * 2, th + pad * 1.4, 14 * self.u,
                      d.get("box_color") or self.col["dark"], 0.15, "\\fad(200,250)", layer=4)
            soft = ""
        self.txt(t0, t1, x, y, "\\N".join(lines), font, fs, d.get("color") or self.col["light"],
                 extra="\\fad(200,250)" + soft, layer=5)

    def hook(self, t0, t1, d):
        u = self.u
        fs = float(d.get("size") or self.sz["hook"])
        maxw = self.W - 2 * 80 * u
        lines = self.wrap("caption", fs, str(d.get("text", "")).upper() if d.get("uppercase", True)
                          else d.get("text", ""), maxw - 60 * u)
        tw = max(self.width("caption", fs, ln) for ln in lines)
        lh = fs * 1.12
        padx, pady = 34 * u, 24 * u
        bw, bh = tw + padx * 2, lh * len(lines) + pady * 2
        x, y = self.anchor(d.get("position"), bw, bh, "top")
        cx, cy = x + bw / 2, y + bh / 2
        pop = "\\fscx70\\fscy70\\t(0,160,\\fscx106\\fscy106)\\t(160,260,\\fscx100\\fscy100)\\fad(80,200)"
        self.draw(t0, t1, cx, cy, bw, bh, 22 * u, d.get("box_color") or self.col["light"], 0, pop, layer=6, an=5)
        self.txt(t0, t1, cx, cy, "\\N".join(lines), "caption", fs, d.get("color") or self.col["dark"],
                 an=5, extra=pop + "\\q2", layer=7)

    # ------------------------------------------------------------------ cards
    def card(self, kind, t0, t1, d):
        u, W, H = self.u, self.W, self.H
        ch = self.b["channel"]
        fo = "\\fad(0,300)"
        if kind == "card_intro":
            name = d.get("title") or self.p.intro.get("title") or ch["name"]
            tag = d.get("subtitle") or self.p.intro.get("subtitle") or ch["tagline"]
            fs, fs2 = self.sz["card_title"], self.sz["card_sub"]
            cy = H * 0.46
            self.txt(t0, t1, W / 2, cy, name, "heading", fs, self.col["light"], an=2,
                     extra="\\fscx92\\fscy92\\t(0,450,0.5,\\fscx100\\fscy100)\\fad(250,300)", layer=5)
            self.draw(t0, t1, W / 2, cy + 22 * u, 260 * u, 8 * u, 4 * u, self.col["primary"], 0,
                      "\\fscx0\\t(200,700,0.5,\\fscx100)" + fo, layer=5, an=8)
            self.txt(t0, t1, W / 2, cy + 58 * u, tag, "body", fs2, self.col["muted"], an=8,
                     extra="\\alpha&HFF&\\t(450,850,\\alpha&H00&)" + fo, layer=5)
        elif kind == "card_outro":
            o = self.p.outro
            title, sub, note = d.get("title") or o.get("title"), d.get("subtitle") or o.get("subtitle"), o.get("note")
            fs, fs2 = self.sz["card_title"] * 0.8, self.sz["card_sub"]
            y = H * 0.12
            self.txt(t0, t1, W / 2, y, title, "heading", fs, self.col["light"], an=8,
                     extra="\\fscx92\\fscy92\\t(0,400,0.5,\\fscx100\\fscy100)\\fad(250,400)", layer=5)
            self.draw(t0, t1, W / 2, y + fs * 1.15, 200 * u, 8 * u, 4 * u, self.col["primary"], 0,
                      "\\fscx0\\t(200,650,0.5,\\fscx100)\\fad(0,400)", layer=5, an=8)
            if sub:
                self.txt(t0, t1, W / 2, y + fs * 1.15 + 34 * u, sub, "body", fs2, self.col["muted"], an=8,
                         extra="\\alpha&HFF&\\t(400,800,\\alpha&H00&)\\fad(0,400)", layer=5)
            if note:
                self.txt(t0, t1, W / 2, H - 70 * u, note, "body", self.sz["callout"] * 0.85, self.col["muted"],
                         an=2, extra="\\alpha&HFF&\\t(700,1100,\\alpha&H40&)\\fad(0,400)", layer=5)
            # centre area left empty on purpose: add YouTube end-screen elements there in YouTube Studio
        else:
            title, sub = d.get("title", ""), d.get("subtitle", "")
            fs = float(d.get("size") or self.sz["card_title"])
            lines = self.wrap("heading", fs, title, W * 0.84)
            fs2 = self.sz["card_sub"]
            total_h = fs * 1.1 * len(lines) + (fs2 * 1.6 if sub else 0)
            y = (H - total_h) / 2
            self.txt(t0, t1, W / 2, y, "\\N".join(lines), "heading", fs, self.col["light"], an=8,
                     extra="\\fscx85\\fscy85\\t(0,260,0.6,\\fscx100\\fscy100)\\fad(150,300)", layer=5)
            if sub:
                self.txt(t0, t1, W / 2, y + fs * 1.1 * len(lines) + 20 * u, sub, "body", fs2,
                         self.col["primary"], an=8, extra="\\alpha&HFF&\\t(200,500,\\alpha&H00&)" + fo, layer=5)

    # ------------------------------------------------------------------ subtitles
    def subtitles(self):
        cfg = self.b["subtitles"][self.fmt]
        cues = self.plan.cues
        if not cues:
            return
        if self.fmt == "long":
            fs = self.sz["subtitles"]
            maxl = int(cfg["max_chars_per_line"])
            for a, b, t in chunk_for_display(cues, maxl * int(cfg.get("max_lines", 2))):
                t = t.upper() if cfg.get("uppercase") else t
                self.add(a, b, "\\N".join(_esc(ln) for ln in wrap_two_lines(t, maxl).split("\\N")), 8, "Sub")
        else:
            fs = self.sz["subtitles"]
            y = self.H * float(cfg.get("position_y", 0.68))
            hl = ass_color_tag(cfg.get("highlight_color", self.col["secondary"]))
            base = ass_color_tag(cfg.get("color", "#FFFFFF"))
            for a, b, t in chunk_for_display(cues, int(cfg["max_chars"]), int(cfg["max_words"])):
                t = t.upper() if cfg.get("uppercase", True) else t
                words = t.split()
                if not words:
                    continue
                longest = max(range(len(words)), key=lambda i: len(words[i].strip(".,!?")))
                if len(words[longest]) >= 4 and cfg.get("highlight", "longest_word") != "none":
                    words[longest] = f"{{\\1c{hl}}}{_esc(words[longest])}{{\\1c{base}}}"
                    words = [w if i == longest else _esc(w) for i, w in enumerate(words)]
                else:
                    words = [_esc(w) for w in words]
                line = " ".join(words)
                if self.width("caption", fs, t) > self.W - 2 * 90 * self.u:
                    mid = len(words) // 2
                    line = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])
                pop = "\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)" if cfg.get("pop_animation", True) else ""
                self.add(a, b, f"{{\\an5\\pos({self.W / 2:.0f},{y:.0f}){pop}}}{line}", 8, "Cap")

    # ------------------------------------------------------------------ build
    def build(self):
        for o in self.plan.overlays:
            t, t0, t1, d = o["type"], o["t0"], o["t1"], o["data"]
            if t.startswith("card_"):
                self.card(t, t0, t1, d)
            else:
                getattr(self, t)(t0, t1, d)
        wm = self.b["channel"].get("watermark") or {}
        if wm.get("enabled") and not (self.b["channel"].get("logo") or {}).get("file"):
            for a, b in self._content_ranges():
                fs = self.sz["watermark"]
                tw = self.width("heading", fs, wm.get("text", ""))
                x, y = self.anchor(wm.get("position", "top-right"), tw, fs, "top-right")
                if self.fmt == "long":
                    y = 44 * self.u if str(wm.get("position", "top")).startswith("top") else y
                self.txt(a, b, x, y, wm.get("text", ""), "heading", fs, self.col["light"],
                         alpha=1 - float(wm.get("opacity", 0.55)), extra="\\fsp2\\shad1\\4a&HA0&\\fad(400,400)",
                         layer=0)
        self.subtitles()

    def _content_ranges(self):
        fps, out = self.plan.fps, []
        for ps in self.plan.scenes:
            if ps.scene.card is not None or ps.scene.auto:
                continue
            a, b = (ps.start_f + ps.trans_f) / fps, (ps.start_f + ps.frames) / fps
            if out and a - out[-1][1] < 1.0:
                out[-1] = (out[-1][0], b)
            else:
                out.append((a, b))
        return out

    def write(self, path: Path):
        sub = self.b["subtitles"][self.fmt]
        fn = self.font_name
        def style(name, font, size, prim, outc="#000000", outa=0.0, bord=0, shad=0, bstyle=1, align=7, mv=0,
                  back="#000000", backa=0.5):
            return (f"Style: {name},{fn[font]},{size:.0f},{ass_color(prim)},{ass_color(prim)},{ass_color(outc, outa)},"
                    f"{ass_color(back, backa)},0,0,0,0,100,100,0,0,{bstyle},{bord},{shad},{align},0,0,{mv:.0f},1")
        styles = [
            style("Base", "body", 40, "#FFFFFF"),
            style("Shape", "body", 20, "#FFFFFF"),
            style("Sub", sub.get("font", "body") if self.fmt == "long" else "body", self.sz["subtitles"],
                  sub.get("color", "#FFFFFF"), sub.get("box_color", "#000000"),
                  1 - float(sub.get("box_opacity", 0.45)), 14 * self.u, 0, 3, 2,
                  sub.get("margin_bottom", 56)),
            style("Cap", sub.get("font", "caption") if self.fmt == "short" else "caption", self.sz["subtitles"],
                  sub.get("color", "#FFFFFF"), sub.get("outline_color", "#000000"), 0,
                  float(sub.get("outline", 7)) * self.u, 3 * self.u, 1, 5, 0, "#000000", 0.45),
        ]
        lines = ["[Script Info]", "; Generated by Smart Finds Lab video system", "ScriptType: v4.00+",
                 f"PlayResX: {self.W}", f"PlayResY: {self.H}", "WrapStyle: 0", "ScaledBorderAndShadow: yes",
                 "YCbCr Matrix: TV.709", "", "[V4+ Styles]",
                 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
                 "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
                 "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding", *styles, "", "[Events]",
                 "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
        for layer, a, b, st, text in sorted(self.events, key=lambda e: (e[1], e[0])):
            lines.append(f"Dialogue: {layer},{_ts(a)},{_ts(b)},{st},,0,0,0,,{text}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
