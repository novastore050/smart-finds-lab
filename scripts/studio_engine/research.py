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
SOURCED_FIELDS = ["name", "brand", "asin", "amazon_url", "price_amazon", "rating_amazon", "review_count_amazon"]


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


def write_reports(prod: Production):
    data = load_research(prod)
    issues = validate(data, int(prod.meta.get("products_wanted", 10)))
    errors = [m for lvl, m in issues if lvl == "error"]
    r = data.get("research") or {}
    srcs = data.get("sources") or {}

    # ---- full report
    L = [f"# Research report — {prod.title}", "",
         f"Market: **{r.get('market', 'Amazon USA')}** · Researched: **{r.get('researched_on', '?')}** · "
         f"By: {r.get('researcher', '?')}", "",
         "> **Important:** values marked ⚠️ *unverified* come from third-party pages (retailers, review sites, "
         "price trackers) and may be out of date. They are **not** confirmed Amazon data. Prices and ratings must "
         "be checked on Amazon.com with the verification sheet before they are used in a video.", ""]
    if r.get("method"):
        L += ["## Method", "", str(r["method"]).strip(), ""]
    if r.get("limitations"):
        L += ["## Limitations", ""] + [f"- {x}" for x in r["limitations"]] + [""]
    if issues:
        L += ["## Data checks", ""] + [f"- {'❌' if lvl == 'error' else '⚠️'} {m}" for lvl, m in issues] + [""]
    for p in products_by_rank(data, ("shortlisted", "reserve", "candidate", "rejected")):
        v = verification_summary(p)
        L += [f"## {('#' + str(p['rank']) + ' — ') if p.get('status') == 'shortlisted' else ''}{fval(p['name'])}",
              "", f"Status: **{p.get('status')}** · Category: {p.get('category', '—')} · Product id: `{p['id']}`", "",
              "| Field | Value | Status | Sources | As of |", "|---|---|---|---|---|"]
        for name, label in (("brand", "Brand"), ("asin", "ASIN"), ("amazon_url", "Amazon URL"),
                            ("price_amazon", "Amazon price"), ("rating_amazon", "Amazon rating"),
                            ("review_count_amazon", "Amazon review count")):
            f = p.get(name) or {}
            val = fval(f)
            if name == "price_amazon" and val not in (None, ""):
                val = _fmt_money(val)
            if name == "rating_amazon" and val not in (None, ""):
                val = f"{val} / 5"
            if name == "review_count_amazon" and val not in (None, ""):
                val = f"{int(val):,}" if str(val).isdigit() else val
            st = v.get(name) or ("verified" if fverified(f) else "unverified" if val else "missing")
            note = f" ({f.get('note')})" if isinstance(f, dict) and f.get("note") else ""
            L.append(f"| {label} | {val if val not in (None, '') else '—'}{note} | {_status_badge(st)} | "
                     f"{_src_links(data, f.get('sources') if isinstance(f, dict) else [])} | "
                     f"{f.get('as_of', '') if isinstance(f, dict) else ''} |")
        for ro in p.get("ratings_other") or []:
            cnt = f" from {int(ro['count']):,} ratings" if ro.get("count") else ""
            L.append(f"| Rating on {ro['platform']} (not Amazon) | {ro['value']} / 5{cnt}"
                     f"{(' (' + ro['note'] + ')') if ro.get('note') else ''} | ⚠️ not Amazon | "
                     f"{_src_links(data, [ro['source']])} | {ro.get('as_of', '')} |")
        for tp in p.get("prices_third_party") or []:
            L.append(f"| Third-party price ({tp.get('seller', '?')}) | {_fmt_money(tp['value'])} | ⚠️ not Amazon | "
                     f"{_src_links(data, [tp['source']])} | {tp.get('as_of', '')} |")
        L.append("")
        for kind, label in (("features", "Key features"), ("pros", "Main benefits (what buyers/reviewers like)"),
                            ("cons", "Disadvantages (common complaints)")):
            if p.get(kind):
                L += [f"**{label}**", ""] + [f"- {it['text']} — {_src_links(data, [it['source']])}" for it in p[kind]] + [""]
        if p.get("best_for"):
            L += [f"**Best for:** {p['best_for']}", ""]
        if p.get("why_selected"):
            L += [f"**Why selected:** {p['why_selected']}", ""]
    L += ["## Sources", "", "Quality: *editorial* = publication with its own testing/reviews · *aggregator* = summarises "
          "other reviews · *affiliate roundup* = earns from sales, often generic text · *retailer* = store page · "
          "*amazon (search index)* = Amazon page as indexed by a search engine, capture date unknown.", "",
          "| ID | Type | Quality | Publisher | Title | Accessed |", "|---|---|---|---|---|---|"]
    for sid, s in srcs.items():
        L.append(f"| {sid} | {s.get('type')} | {s.get('quality', '')} | {s.get('publisher', '')} | "
                 f"[{s.get('title', s['url'])}]({s['url']}) | {s.get('accessed')} |")
    prod.p("research", "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # ---- ranked shortlist
    short = products_by_rank(data)
    S = [f"# Product shortlist — {prod.title}", "",
         f"Research date: {r.get('researched_on', '?')} · Video type: **{prod.meta.get('video_type')}** "
         "(research-based: no hands-on testing claims)", "",
         "Ranked as a countdown: #10 is shown first, #1 last.", "",
         "| Rank | Product | Brand | ASIN | Amazon price | Third-party price (date) | Reported Amazon rating | Verification |",
         "|---|---|---|---|---|---|---|---|"]
    for p in short:
        v = verification_summary(p)
        tps = p.get("prices_third_party") or []
        tp = "; ".join(f"{_fmt_money(t['value'])} {t.get('seller', '')} ({t.get('as_of', '')})" for t in tps[:2]) or "—"
        rat = fval(p.get("rating_amazon"))
        cnt = fval(p.get("review_count_amazon"))
        rating = (f"{rat}★" if rat else "—") + (f" / {int(cnt):,} ratings" if cnt and str(cnt).isdigit() else "")
        if not rat and p.get("ratings_other"):
            ro = p["ratings_other"][0]
            rating = f"— (on {ro['platform']}: {ro['value']}★{' / ' + format(int(ro['count']), ',') if ro.get('count') else ''})"
        n_ver = sum(1 for k in ("asin", "price_amazon", "rating_amazon", "review_count_amazon") if v[k] == "verified")
        url = fval(p.get("amazon_url"))
        name = f"[{fval(p['name'])}]({url})" if url else fval(p["name"])
        ap = fval(p.get("price_amazon"))
        ap = (_fmt_money(ap) + (" ✅" if fverified(p.get("price_amazon")) else " (snapshot, unverified)")) if ap else \
            "— (check on Amazon)"
        S.append(f"| #{p['rank']} | {name} | {fval(p.get('brand')) or '—'} | {fval(p.get('asin')) or '—'} | {ap} | {tp} | "
                 f"{rating} {'(unverified)' if rat and not fverified(p.get('rating_amazon')) else ''} | {n_ver}/4 verified |")
    S += ["", "### Why this order", ""] + [f"- **#{p['rank']} {fval(p['name'])}**: {p.get('why_selected', '—')}" for p in short]
    reserves = products_by_rank(data, ("reserve",))
    if reserves:
        S += ["", "### Reserves (can replace a product you reject)", ""] + \
             [f"- {fval(p['name'])} — {p.get('why_selected', '')}" for p in reserves]
    S += ["", "## What you need to do", "",
          "1. Open `research/amazon-verification.csv` (or the .md version) and check each product on Amazon.com: "
          "is it the right product, available in the US, and what are the **current** price, rating and number of ratings.",
          "2. Fill in the columns, then run:", "",
          f"   `python scripts/studio.py import-verification {prod.slug}`", "",
          "3. If you are happy with the products (you can approve before or after verifying), run:", "",
          f"   `python scripts/studio.py approve-products {prod.slug}`", "",
          "Nothing that costs money (voice, video generation) happens before approval."]
    if errors:
        S += ["", "## ❌ Data errors to fix first", ""] + [f"- {e}" for e in errors]
    prod.p("research", "shortlist.md").write_text("\n".join(S) + "\n", encoding="utf-8")

    # ---- verification sheet
    write_verification_sheet(prod, data)
    return issues


VER_COLS = ["product_id", "rank", "product_name", "amazon_link", "asin_found", "third_party_price_for_reference",
            "correct_product_yes_no", "available_in_us_yes_no", "amazon_price_usd", "amazon_rating",
            "amazon_rating_count", "asin_confirmed_or_corrected", "amazon_url_if_different", "checked_on_yyyy_mm_dd",
            "notes"]


def write_verification_sheet(prod: Production, data: dict):
    path = prod.p("research", "amazon-verification.csv")
    old = {}
    if path.exists():  # keep anything the owner already typed in
        with open(path, newline="", encoding="utf-8") as fh:
            old = {row["product_id"]: row for row in csv.DictReader(fh)}
    rows = []
    for p in products_by_rank(data, ("shortlisted", "reserve")):
        url = fval(p.get("amazon_url"))
        asin = fval(p.get("asin"))
        link = url or (f"https://www.amazon.com/s?k={str(fval(p['name'])).replace(' ', '+')}")
        tps = p.get("prices_third_party") or []
        row = {"product_id": p["id"], "rank": p.get("rank") if p.get("status") == "shortlisted" else "reserve",
               "product_name": fval(p["name"]), "amazon_link": link, "asin_found": asin or "",
               "third_party_price_for_reference": "; ".join(f"{_fmt_money(t['value'])} {t.get('seller', '')} "
                                                             f"({t.get('as_of', '')})" for t in tps[:2])}
        for c in VER_COLS:
            row.setdefault(c, "")
            if c in old.get(p["id"], {}) and old[p["id"]][c] and c not in ("rank", "product_name", "amazon_link",
                                                                            "asin_found", "third_party_price_for_reference"):
                row[c] = old[p["id"]][c]
        rows.append(row)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=VER_COLS)
        w.writeheader()
        w.writerows(rows)
    M = [f"# Amazon verification sheet — {prod.title}", "",
         "Open each link **on Amazon.com (USA)** and fill the matching row in `amazon-verification.csv` "
         "(Excel, Google Sheets or Numbers can open it; save it as CSV again).", "",
         "Check: right product? · available in the US? · current price · star rating · number of ratings · ASIN "
         "(shown under 'Product information' on the page).", "",
         "| # | Product | Amazon link | ASIN found | Third-party price (reference only) |", "|---|---|---|---|---|"]
    for r in rows:
        M.append(f"| {r['rank']} | {r['product_name']} | [open]({r['amazon_link']}) | {r['asin_found'] or '—'} | "
                 f"{r['third_party_price_for_reference'] or '—'} |")
    M += ["", "When done:", "", f"```bash\npython scripts/studio.py import-verification {prod.slug}\n```", "",
          "*Links without an ASIN are Amazon searches: pick the exact product and paste its URL in "
          "`amazon_url_if_different`.*"]
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
