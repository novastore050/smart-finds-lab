"""Shared helpers for the production studio: production folders, YAML I/O, sourced fields, stages."""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import yaml

from sfl_engine.util import ROOT, SFLError, rel, slugify

PRODUCTIONS = ROOT / "productions"

# The pipeline, in order. Each stage is recorded in production.yaml when completed.
STAGES = [
    ("research", "Product research collected (products.yaml)"),
    ("research_report", "Research report, shortlist and Amazon verification sheet generated"),
    ("products_approved", "Owner approved the product shortlist  (MANUAL)"),
    ("script", "Script written and checked"),
    ("prompts", "Scene prompts + shot list generated"),
    ("voice", "Voice-over files imported for every scene"),
    ("clips", "Clips / photos imported for every shot"),
    ("timeline", "Editing timeline + Shorts file generated"),
    ("render", "Long video rendered"),
    ("shorts", "3 Shorts rendered"),
    ("thumbnail", "Thumbnails generated"),
    ("seo", "SEO pack generated"),
    ("qc", "Final production QC report generated"),
    ("human_review", "Owner watched the final video and approved it  (MANUAL)"),
]


def today() -> str:
    return dt.date.today().isoformat()


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise SFLError(f"File not found: {rel(path)}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise SFLError(f"Typing mistake in {rel(path)}:\n{e}")
    return data


def save_yaml(path: Path, data: dict, header: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)
    path.write_text((header + "\n" if header else "") + text, encoding="utf-8")


class Production:
    """One video project: productions/<slug>/"""

    def __init__(self, slug: str):
        self.slug = slugify(slug)
        self.dir = PRODUCTIONS / self.slug
        if not (self.dir / "production.yaml").exists():
            raise SFLError(f"No production '{self.slug}'. Create it with: python scripts/studio.py new \"Title\"")
        self.meta = load_yaml(self.dir / "production.yaml")

    # ---- paths
    def p(self, *parts) -> Path:
        return self.dir.joinpath(*parts)

    @property
    def title(self):
        return self.meta.get("title", self.slug)

    @property
    def video_dir(self):
        return ROOT / "assets" / "video" / self.slug

    @property
    def image_dir(self):
        return ROOT / "assets" / "images" / self.slug

    # ---- stages
    def reload(self):
        self.meta = load_yaml(self.dir / "production.yaml")

    def done(self, stage: str) -> bool:
        self.reload()  # another command may have updated production.yaml
        return bool((self.meta.get("stages") or {}).get(stage))

    def mark(self, stage: str, note: str = ""):
        self.reload()
        self.meta.setdefault("stages", {})[stage] = {"at": now(), **({"note": note} if note else {})}
        self.save()

    def unmark(self, stage: str):
        self.reload()
        (self.meta.get("stages") or {}).pop(stage, None)
        self.save()

    def save(self):
        save_yaml(self.dir / "production.yaml", self.meta,
                  "# Production settings and progress. Stages are recorded automatically.")

    def require(self, stage: str, force=False, why=""):
        if not self.done(stage) and not force:
            label = dict(STAGES)[stage]
            raise SFLError(f"Stage not done yet: {label}.{(' ' + why) if why else ''}")


def create_production(title: str, video_type: str = "research_based", slug: str | None = None) -> Production:
    slug = slugify(slug or title)[:50]
    d = PRODUCTIONS / slug
    if (d / "production.yaml").exists():
        raise SFLError(f"Production already exists: {rel(d)}")
    for sub in ("research", "script", "prompts", "voice", "edit", "seo", "reports", "thumbnails"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    meta = {
        "title": title,
        "slug": slug,
        "created": today(),
        "video_type": video_type,   # research_based | hands_on
        "market": "Amazon USA",
        "audience": "US (also UK, Canada, Australia)",
        "products_wanted": 10,
        "topic_noun": "gadgets",    # used in the draft hook, e.g. "kitchen gadgets", "cleaning tools"
        "music": {"file": None, "license": None},
        "stages": {},
    }
    save_yaml(d / "production.yaml", meta, "# Production settings and progress. Stages are recorded automatically.")
    return Production(slug)


# ---------------------------------------------------------------------------- sourced fields
# A research value is stored as:
#   {value: ..., verified: false, sources: [S1, S3], as_of: 2026-11-03, note: "..."}
# verified: true ONLY when the value was confirmed on the Amazon.com product page itself
# (by the owner via the verification sheet, or by an official Amazon API).

ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
AMAZON_URL_RE = re.compile(r"^https://www\.amazon\.com/(?:[^/]+/)?dp/([A-Z0-9]{10})(?:[/?].*)?$")


def fval(field):
    """Value of a sourced field (or a plain value)."""
    if isinstance(field, dict) and "value" in field:
        return field.get("value")
    return field


def fverified(field) -> bool:
    return bool(isinstance(field, dict) and field.get("verified"))


def asin_from_url(url: str | None):
    m = AMAZON_URL_RE.match(str(url or ""))
    return m.group(1) if m else None
