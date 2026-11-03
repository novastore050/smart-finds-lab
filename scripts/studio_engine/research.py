"""Product research: validation, report, ranked shortlist, Amazon verification sheet, approval.

The research data lives in productions/<slug>/research/products.yaml. Every value records
its sources, the date it was found, and whether it is VERIFIED (confirmed on the Amazon.com
product page) or UNVERIFIED (from third-party pages, or not yet checked).
Nothing here invents data: empty fields stay empty and are shown as "not collected".
"""
from __future__ import annotations

import csv
from pathlib import Path

from sfl_engine.util import SFLError, rel

from .common import (AMAZON_URL_RE, ASIN_RE, Production, asin_from_url, fval, fverified, load_yaml, save_yaml,
                     today)

SOURCE_TYPES = {"amazon", "owner_check", "manufacturer", "third_party", "editorial_review", "retailer",
                "amazon_search_index"}  # amazon_search_index = Amazon page seen only via a search engine (date unknown)
VERIFYING_TYPES = {"amazon", "owner_check"}  # only these can make a field "verified"
SOURCED_FIELDS = ["name", "brand", "model", "asin", "amazon_url", "price_amazon", "rating_amazon",
                  "review_count_amazon"]
AMAZON_FIELDS = {"asin", "amazon_url", "price_amazon", "rating_amazon", "review_count_amazon"}
AMAZON_SOURCE_TYPES = {"amazon", "owner_check", "amazon_search_index"}
SCORE_KEYS = [("evidence", "Evidence"), ("visual", "Visual demo"), ("everyday", "Everyday benefit"),
              ("problem", "Clear problem/solution")]


def load_research(prod: Production) -> dict:
    return load_yaml(prod.p("research", "products.yaml"))


def save_research(prod: Production, data: dict):
    save_yaml(prod.p("research", "products.yaml"), data,
              "# Product research. Every value has sources + date + verified flag.\n"
              "# verified: true ONLY after checking the Amazon.com product page (see amazon-verification.csv).")


def products_by_rank(data: dict, statuses=("shortlisted",)):
    ps = [p for p in data.get("products", []) if p.get("status") in statuses]
    return sorted(ps, key=lambda p: (p.get("rank") or 999))


def _fmt_money(v):
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


# ---------------------------------------------------------------------------- validation
def validate(data: dict, wanted: int = 10):
    issues = []  # (level, message)
    sources = data.get("sources") or {}
    for sid, s in sources.items():
        if not s.get("url"):
            issues.append(("error", f"source {sid} has no url"))
        if s.get("type") not in SOURCE_TYPES:
            issues.append(("error", f"source {sid}: type must be one of {sorted(SOURCE_TYPES)}"))
        if not s.get("accessed"):
            issues.append(("error", f"source {sid} has no 'accessed' date"))

    def check_field(pid, name, f):
        if not isinstance(f, dict):
            issues.append(("error", f"{pid}.{name}: must be {{value, verified, sources, as_of}}"))
            return
        if f.get("value") in (None, "", []):
            return
        srcs = f.get("sources") or []
        if not srcs:
            issues.append(("error", f"{pid}.{name}: value has no source"))
        for s in srcs:
            if s not in sources:
                issues.append(("error", f"{pid}.{name}: unknown source id {s}"))
        if not f.get("as_of"):
            issues.append(("error", f"{pid}.{name}: missing as_of date"))
        if f.get("verified") and not any(sources.get(s, {}).get("type") in VERIFYING_TYPES for s in srcs):
            issues.append(("error", f"{pid}.{name}: marked verified but no Amazon/owner-check source"))
        if name in AMAZON_FIELDS and any(sources.get(s, {}).get("type") not in AMAZON_SOURCE_TYPES for s in srcs):
            issues.append(("error", f"{pid}.{name}: Amazon fields may only cite Amazon pages - put third-party "
                                    "figures in ratings_other / prices_third_party"))

    ids = set()
    for p in data.get("products", []):
        pid = p.get("id", "?")
        if pid in ids:
            issues.append(("error", f"duplicate product id {pid}"))
        ids.add(pid)
        for name in SOURCED_FIELDS:
            if name in p:
                check_field(pid, name, p[name])
        if not fval(p.get("name")):
            issues.append(("error", f"{pid}: no product name"))
        asin, url = fval(p.get("asin")), fval(p.get("amazon_url"))
        if asin and not ASIN_RE.match(str(asin)):
            issues.append(("error", f"{pid}: ASIN '{asin}' is not 10 letters/digits"))
        if url and not AMAZON_URL_RE.match(str(url)):
            issues.append(("warning", f"{pid}: amazon_url is not a standard amazon.com/dp/ASIN link"))
        if asin and url and asin_from_url(url) and asin_from_url(url) != asin:
            issues.append(("error", f"{pid}: ASIN {asin} does not match the URL ({asin_from_url(url)})"))
        for tp in p.get("prices_third_party") or []:
            if not tp.get("source") or tp.get("source") not in sources or not tp.get("as_of"):
                issues.append(("error", f"{pid}: third-party price {tp.get('value')} needs a known source + as_of"))
        for ro in p.get("ratings_other") or []:
            if ro.get("source") not in sources or not ro.get("as_of") or not ro.get("platform"):
                issues.append(("error", f"{pid}: rating on another platform needs platform + known source + as_of"))
        for kind in ("features", "pros", "cons"):
            for it in p.get(kind) or []:
                if not it.get("source"):
                    issues.append(("error", f"{pid}.{kind}: '{it.get('text', '')[:40]}' has no source"))
                elif it["source"] not in sources:
                    issues.append(("error", f"{pid}.{kind}: unknown source {it['source']}"))
        if p.get("status") == "shortlisted":
            if not (p.get("pros") and p.get("cons")):
                issues.append(("warning", f"{pid}: shortlisted products need at least one pro and one con"))
            if not url:
                issues.append(("warning", f"{pid}: no Amazon URL found yet - find it during verification"))
    short = products_by_rank(data)
    if len(short) != wanted:
        issues.append(("warning", f"{len(short)} products shortlisted, {wanted} wanted"))
    ranks = [p.get("rank") for p in short]
    if sorted(ranks) != list(range(1, len(short) + 1)):
        issues.append(("error", f"shortlist ranks must be 1..{len(short)} with no gaps (got {ranks})"))
    return issues


def verification_summary(p: dict):
    out = {}
    for name in ("asin", "amazon_url", "price_amazon", "rating_amazon", "review_count_amazon"):
        f = p.get(name) or {}
        if fverified(f):
            out[name] = "verified"
        elif fval(f) not in (None, ""):
            out[name] = "unverified"
        else:
            out[name] = "missing"
    return out


def _status_badge(s):
    return {"verified": "✅ verified", "unverified": "⚠️ unverified", "missing": "— not collected"}[s]


# ---------------------------------------------------------------------------- reports
def _src_links(data, ids):
    srcs = data.get("sources") or {}
    out = []
    for s in ids or []:
        if s in srcs:
            out.append(f"[{s}]({srcs[s]['url']})")
        else:
            out.append(s)
    return ", ".join(out)


def countdown(data: dict):
    """Shortlisted products in VIDEO order: #10 first ... #1 (strongest) last."""
    return list(reversed(products_by_rank(data)))


def _fmtv(name, f):
    val = fval(f)
    if val in (None, ""):
        return "—"
    if name == "price_amazon":
        return _fmt_money(val)
    if name == "rating_amazon":
        return f"{val} / 5"
    if name == "review_count_amazon":
        return f"{int(val):,}" if str(val).isdigit() else str(val)
    return str(val)


def _score(p):
    sc = p.get("scores") or {}
    return sum(int(sc.get(k, 0)) for k, _ in SCORE_KEYS)


def _row(data, label, name, f):
    st = "verified" if fverified(f) else ("unverified" if fval(f) not in (None, "") else "missing")
    note = f" ({f.get('note')})" if isinstance(f, dict) and f.get("note") else ""
    srcs = f.get("sources") if isinstance(f, dict) else []
    asof = f.get("as_of", "") if isinstance(f, dict) else ""
    return f"| {label} | {_fmtv(name, f)}{note} | {_status_badge(st)} | {_src_links(data, srcs)} | {asof or ''} |"


def write_reports(prod: Production):
    data = load_research(prod)
    issues = validate(data, int(prod.meta.get("products_wanted", 10)))
    errors = [m for lvl, m in issues if lvl == "error"]
    r = data.get("research") or {}
    srcs = data.get("sources") or {}

    # ---- full report (shortlist in countdown order, then reserves/rejected)
    L = [f"# Research report — {prod.title}", "",
         f"Market: **{r.get('market', 'Amazon USA')}** · Researched: **{r.get('researched_on', '?')}** · "
         f"By: {r.get('researcher', '?')}" + (f" · Revision: {r.get('revision')}" if r.get("revision") else ""), "",
         "> **Important:** nothing below has been checked on the live Amazon.com page yet. **Amazon data** comes "
         "from Amazon pages as seen through a search engine (capture date unknown). **Third-party data** comes "
         "from other sites and is never Amazon data. Both are ⚠️ unverified until you check them with the "
         "verification sheet.", ""]
    if r.get("changes"):
        L += ["## Changes in this revision", ""] + [f"- {x}" for x in r["changes"]] + [""]
    if r.get("method"):
        L += ["## Method", "", str(r["method"]).strip(), ""]
    if r.get("scoring"):
        L += ["## How the ranking works", "", str(r["scoring"]).strip(), ""]
    if r.get("limitations"):
        L += ["## Limitations", ""] + [f"- {x}" for x in r["limitations"]] + [""]
    if issues:
        L += ["## Data checks", ""] + [f"- {'❌' if lvl == 'error' else '⚠️'} {m}" for lvl, m in issues] + [""]
    others = [p for p in data.get("products", []) if p.get("status") != "shortlisted"]
    for p in countdown(data) + others:
        head = f"#{p['rank']} — " if p.get("status") == "shortlisted" else f"[{p.get('status')}] "
        L += [f"## {head}{fval(p['name'])}", "",
              f"Brand: **{fval(p.get('brand')) or '—'}** · Model: **{fval(p.get('model')) or '—'}** · "
              f"Category: {p.get('category', '—')} · Product id: `{p['id']}`"
              + (f" · Score: **{_score(p)}/20**" if p.get("scores") else ""), ""]
        if p.get("status") in ("rejected",) and p.get("rejected_reason"):
            L += [f"**Why removed:** {p['rejected_reason']}", ""]
        L += ["**Amazon data** (from Amazon pages via search engine — not yet checked live)", "",
              "| Field | Value | Status | Source | As of |", "|---|---|---|---|---|"]
        for name, label in (("asin", "ASIN"), ("amazon_url", "Amazon URL"), ("model", "Model (listing)"),
                            ("price_amazon", "Price"), ("rating_amazon", "Star rating"),
                            ("review_count_amazon", "Number of ratings")):
            L.append(_row(data, label, name, p.get(name) or {}))
        for note in p.get("amazon_notes") or []:
            L.append(f"| Listing note | {note['text']} | ⚠️ unverified | {_src_links(data, [note['source']])} | "
                     f"{note.get('as_of', '')} |")
        L += ["", "**Third-party data** (other websites — never Amazon data)", ""]
        tp_rows = []
        for ro in p.get("ratings_other") or []:
            cnt = f" from {int(ro['count']):,} ratings" if ro.get("count") else ""
            tp_rows.append(f"| Rating — {ro['platform']} | {ro['value']} / 5{cnt}"
                           f"{(' (' + ro['note'] + ')') if ro.get('note') else ''} | "
                           f"{_src_links(data, [ro['source']])} | {ro.get('as_of', '')} |")
        for tp in p.get("prices_third_party") or []:
            tp_rows.append(f"| Price — {tp.get('seller', '?')} | {_fmt_money(tp['value'])} | "
                           f"{_src_links(data, [tp['source']])} | {tp.get('as_of', '')} |")
        if tp_rows:
            L += ["| Item | Value | Source | As of |", "|---|---|---|---|"] + tp_rows
        else:
            L.append("*No third-party ratings or prices recorded.*")
        L.append("")
        if p.get("scores"):
            sc = p["scores"]
            L += ["**Selection score:** " + " · ".join(f"{lab} {sc.get(k, 0)}/5" for k, lab in SCORE_KEYS)
                  + f" = **{_score(p)}/20**", ""]
        for kind, label in (("features", "Key features"), ("pros", "Main benefits (what buyers/reviewers like)"),
                            ("cons", "Disadvantages (common complaints)")):
            if p.get(kind):
                L += [f"**{label}**", ""] + [f"- {it['text']} — {_src_links(data, [it['source']])}" for it in p[kind]] + [""]
        if p.get("best_for"):
            L += [f"**Best for:** {p['best_for']}", ""]
        if p.get("why_selected"):
            L += [f"**Why selected:** {p['why_selected']}", ""]
        if p.get("verify_notes"):
            L += ["**Check on Amazon:** " + "; ".join(p["verify_notes"]), ""]
    L += ["## Sources", "", "Quality: *editorial* = publication with its own testing/reviews · *aggregator* = summarises "
          "other reviews · *affiliate roundup* = earns from sales, often generic text · *retailer* = store page · "
          "*amazon (search index)* = Amazon page as indexed by a search engine, capture date unknown.", "",
          "| ID | Type | Quality | Publisher | Title | Accessed |", "|---|---|---|---|---|---|"]
    for sid, s in srcs.items():
        L.append(f"| {sid} | {s.get('type')} | {s.get('quality', '')} | {s.get('publisher', '')} | "
                 f"[{s.get('title', s['url'])}]({s['url']}) | {s.get('accessed')} |")
    prod.p("research", "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---- ranked shortlist, in the order the video shows them
    S = [f"# Product shortlist — {prod.title}", "",
         f"Research date: {r.get('researched_on', '?')}" + (f" (revision {r.get('revision')})" if r.get("revision") else "")
         + f" · Video type: **{prod.meta.get('video_type')}** (research-based: no hands-on testing claims)", "",
         "**Countdown order — exactly as the video plays: #10 first, #1 (strongest) last.**", "",
         "⚠️ No Amazon value is verified yet. *Amazon data* = Amazon page seen via search engine (date unknown). "
         "*Third-party data* = other sites.", "",
         "| Video order | Rank | Product | Brand · Model | ASIN | Amazon data (unverified) | Third-party data | Score |",
         "|---|---|---|---|---|---|---|---|"]
    for i, p in enumerate(countdown(data), 1):
        url = fval(p.get("amazon_url"))
        name = f"[{fval(p['name'])}]({url})" if url else fval(p["name"])
        rat, cnt, ap = fval(p.get("rating_amazon")), fval(p.get("review_count_amazon")), fval(p.get("price_amazon"))
        amz = []
        approx = "≈" if any(w in str((p.get("review_count_amazon") or {}).get("note", "")) for w in ("rough", "round")) else ""
        if rat:
            amz.append(f"{rat}★" + (f" ({approx}{int(cnt):,} ratings)" if cnt and str(cnt).isdigit() else ""))
        else:
            amz.append("rating not found")
        if ap:
            amz.append(f"price {_fmt_money(ap)}")
        amz = "; ".join(amz)
        tp = []
        for ro in (p.get("ratings_other") or [])[:2]:
            tp.append(f"{ro['value']}★" + (f"/{int(ro['count']):,}" if ro.get("count") else "") + f" ({ro['platform']})")
        for t in (p.get("prices_third_party") or [])[:1]:
            tp.append(f"{_fmt_money(t['value'])} ({t.get('seller', '')})")
        S.append(f"| {i} | **#{p['rank']}** | {name} | {fval(p.get('brand')) or '—'} · {fval(p.get('model')) or '—'} | "
                 f"{fval(p.get('asin')) or '—'} | {amz} | {'; '.join(tp) or '—'} | {_score(p)}/20 |")
    S += ["", "Score = Evidence + Visual demo + Everyday benefit + Clear problem/solution (each 1–5). "
          "Ties go to the stronger evidence.", "", "### Why each product (countdown order)", ""]
    for p in countdown(data):
        S.append(f"- **#{p['rank']} {fval(p['name'])}** — {p.get('why_selected', '—')}")
        if p.get("verify_notes"):
            S.append(f"  - *Check on Amazon:* {'; '.join(p['verify_notes'])}")
    if r.get("changes"):
        S += ["", "### Changes from the previous shortlist", ""] + [f"- {x}" for x in r["changes"]]
    reserves = products_by_rank(data, ("reserve",))
    if reserves:
        S += ["", "### Reserves (can replace a product you reject)", ""] + \
             [f"- {fval(p['name'])} — {p.get('why_selected', '')}" for p in reserves]
    S += ["", "## What you need to do", "",
          "1. Open `research/amazon-verification.csv` (same countdown order) and check each product on Amazon.com: "
          "right product and model? available in the US? **current** price, rating and number of ratings.",
          "2. Fill in the columns, then run:", "", f"   `python scripts/studio.py import-verification {prod.slug}`", "",
          "3. If you are happy with the products, run:", "", f"   `python scripts/studio.py approve-products {prod.slug}`",
          "", "Nothing that costs money (voice, video generation) happens before approval."]
    if errors:
        S += ["", "## ❌ Data errors to fix first", ""] + [f"- {e}" for e in errors]
    prod.p("research", "shortlist.md").write_text("\n".join(S) + "\n", encoding="utf-8")
    write_verification_sheet(prod, data)
    return issues


VER_COLS = ["video_order", "rank", "product_id", "product_name", "brand", "model_on_listing", "amazon_link",
            "asin_found", "amazon_rating_found_unverified", "third_party_price_for_reference", "what_to_check",
            "correct_product_yes_no", "available_in_us_yes_no", "amazon_price_usd", "amazon_rating",
            "amazon_rating_count", "asin_confirmed_or_corrected", "amazon_url_if_different", "checked_on_yyyy_mm_dd",
            "notes"]
OWNER_COLS = {"correct_product_yes_no", "available_in_us_yes_no", "amazon_price_usd", "amazon_rating",
              "amazon_rating_count", "asin_confirmed_or_corrected", "amazon_url_if_different", "checked_on_yyyy_mm_dd",
              "notes"}


def write_verification_sheet(prod: Production, data: dict):
    path = prod.p("research", "amazon-verification.csv")
    old = {}
    if path.exists():  # keep anything the owner already typed in
        with open(path, newline="", encoding="utf-8-sig") as fh:
            old = {row.get("product_id"): row for row in csv.DictReader(fh)}
    rows = []
    ordered = [(i, p) for i, p in enumerate(countdown(data), 1)] + \
              [("reserve", p) for p in products_by_rank(data, ("reserve",))]
    for order, p in ordered:
        url = fval(p.get("amazon_url"))
        link = url or (f"https://www.amazon.com/s?k={str(fval(p['name'])).replace(' ', '+')}")
        tps = p.get("prices_third_party") or []
        rat, cnt = fval(p.get("rating_amazon")), fval(p.get("review_count_amazon"))
        row = {"video_order": order, "rank": p.get("rank") if p.get("status") == "shortlisted" else "reserve",
               "product_id": p["id"], "product_name": fval(p["name"]), "brand": fval(p.get("brand")) or "",
               "model_on_listing": fval(p.get("model")) or "", "amazon_link": link,
               "asin_found": fval(p.get("asin")) or "",
               "amazon_rating_found_unverified": (f"{rat} ({int(cnt):,})" if rat and cnt and str(cnt).isdigit()
                                                  else (str(rat) if rat else "")),
               "third_party_price_for_reference": "; ".join(f"{_fmt_money(t['value'])} {t.get('seller', '')} "
                                                             f"({t.get('as_of', '')})" for t in tps[:2]),
               "what_to_check": "; ".join(p.get("verify_notes") or [])}
        for c in VER_COLS:
            row.setdefault(c, "")
            prev = old.get(p["id"], {})
            if c in OWNER_COLS and prev.get(c):
                row[c] = prev[c]
        rows.append(row)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=VER_COLS)
        w.writeheader()
        w.writerows(rows)
    M = [f"# Amazon verification sheet — {prod.title}", "",
         "Open each link **on Amazon.com (USA)** and fill the matching row in `amazon-verification.csv` "
         "(Excel, Google Sheets or Numbers can open it; save it as CSV again). Rows are in countdown order.", "",
         "Check: right product and model? · available in the US? · current price · star rating · number of ratings · "
         "ASIN (under 'Product information').", "",
         "| Order | Rank | Product | Model | Amazon link | ASIN found | What to check |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        M.append(f"| {r['video_order']} | {r['rank']} | {r['product_name']} | {r['model_on_listing'] or '—'} | "
                 f"[open]({r['amazon_link']}) | {r['asin_found'] or '—'} | {r['what_to_check'] or '—'} |")
    M += ["", "When done:", "", f"```bash\npython scripts/studio.py import-verification {prod.slug}\n```"]
    prod.p("research", "amazon-verification.md").write_text("\n".join(M) + "\n", encoding="utf-8")
    return path


def import_verification(prod: Production, log):
    path = prod.p("research", "amazon-verification.csv")
    if not path.exists():
        raise SFLError("No verification sheet yet - run: python scripts/studio.py research-report " + prod.slug)
    data = load_research(prod)
    by_id = {p["id"]: p for p in data.get("products", [])}
    sources = data.setdefault("sources", {})
    changed = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        p = by_id.get(row.get("product_id", ""))
        if not p:
            log.warn(f"row for unknown product id '{row.get('product_id')}' skipped")
            continue
        date = (row.get("checked_on_yyyy_mm_dd") or "").strip()
        filled = [c for c in ("amazon_price_usd", "amazon_rating", "amazon_rating_count", "asin_confirmed_or_corrected",
                              "amazon_url_if_different", "correct_product_yes_no") if (row.get(c) or "").strip()]
        if not filled:
            continue
        if not date:
            log.warn(f"{p['id']}: values filled but no checked_on date - skipped (the date is required)")
            continue
        url = (row.get("amazon_url_if_different") or "").strip() or fval(p.get("amazon_url")) or row.get("amazon_link")
        sid = f"OWNER-{p['id']}-{date}"
        sources[sid] = {"url": url, "type": "owner_check", "publisher": "Amazon.com (checked by channel owner)",
                        "title": f"Owner check of {fval(p['name'])}", "accessed": date}

        def setf(name, value, cast=str):
            nonlocal changed
            try:
                value = cast(str(value).replace("$", "").replace(",", "").strip())
            except ValueError:
                log.warn(f"{p['id']}: could not read {name} = '{value}' - skipped")
                return
            p[name] = {"value": value, "verified": True, "sources": [sid], "as_of": date}
            changed += 1

        if (row.get("amazon_price_usd") or "").strip():
            setf("price_amazon", row["amazon_price_usd"], float)
        if (row.get("amazon_rating") or "").strip():
            setf("rating_amazon", row["amazon_rating"], float)
        if (row.get("amazon_rating_count") or "").strip():
            setf("review_count_amazon", row["amazon_rating_count"], int)
        asin = (row.get("asin_confirmed_or_corrected") or "").strip().upper()
        if asin:
            if not ASIN_RE.match(asin):
                log.warn(f"{p['id']}: '{asin}' is not a valid ASIN - skipped")
            else:
                setf("asin", asin)
        if (row.get("amazon_url_if_different") or "").strip() or asin:
            setf("amazon_url", url)
        yn = (row.get("correct_product_yes_no") or "").strip().lower()
        if yn.startswith("n"):
            p["status"] = "rejected"
            p["rejected_reason"] = f"owner check {date}: not the right product. {row.get('notes', '')}".strip()
            log.info(f"   {p['id']}: marked REJECTED (owner said wrong product)")
        if (row.get("available_in_us_yes_no") or "").strip().lower().startswith("n"):
            p["status"] = "rejected"
            p["rejected_reason"] = f"owner check {date}: not available in the US"
            log.info(f"   {p['id']}: marked REJECTED (not available in the US)")
        if (row.get("notes") or "").strip():
            p["owner_notes"] = row["notes"].strip()
    save_research(prod, data)
    log.info(f"Imported verification: {changed} field(s) are now verified.")
    return changed


def approve(prod: Production, log, note=""):
    prod.require("research_report", why="Run research-report first.")
    data = load_research(prod)
    issues = validate(data, int(prod.meta.get("products_wanted", 10)))
    errors = [m for lvl, m in issues if lvl == "error"]
    if errors:
        raise SFLError("Fix the research data errors first:\n  - " + "\n  - ".join(errors))
    short = products_by_rank(data)
    unver = [fval(p["name"]) for p in short if verification_summary(p)["price_amazon"] != "verified"]
    prod.meta["approved_products"] = [p["id"] for p in short]
    prod.save()
    prod.mark("products_approved", note or f"{len(short)} products approved by owner")
    log.info(f"Approved {len(short)} products.")
    if unver:
        log.info(f"Note: {len(unver)} product(s) still have no verified Amazon price/rating. The script will not "
                 "mention prices or star ratings for them until verified.")
