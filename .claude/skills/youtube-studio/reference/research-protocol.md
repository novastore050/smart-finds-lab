# Research protocol (stage 2)

Goal: `productions/<slug>/research/products.yaml` with N shortlisted products + 2 reserves, every value sourced.

## How to research (Claude, in session)

1. **Candidates:** WebSearch for popular, genuinely useful products in the topic (best-seller lists,
   editorial roundups). Prefer: everyday usefulness, price under ~$50, strong review volume, visual potential.
2. **Amazon listing:** WebSearch with `allowed_domains: ["amazon.com"]`, e.g. `"<brand> <product> amazon.com"`.
   Take the ASIN from a `/dp/<ASIN>` URL. Record that page as a source with
   `type: amazon_search_index` (seen via search engine, date unknown → never "verified").
   If the listing says "currently unavailable", pick an in-stock variant and say so in `why_selected`.
3. **Evidence:** WebSearch for reviews ("<product> review pros cons"). Prefer editorial/hands-on reviews
   (Serious Eats, Wirecutter, America's Test Kitchen / Cook's Illustrated, Tom's Guide, Reviewed) over
   affiliate roundups. Record each page as a source with an honest `quality` label.
4. **Ratings:** an Amazon rating "as reported by" a third party → `rating_amazon` with a `note` naming
   who reported it. Ratings on other stores → `ratings_other` (platform, value, count). If a figure came
   from a search summary and you cannot tell which page said it, write "attribution unconfirmed".
5. **Prices:** Amazon prices seen in search snapshots → `price_amazon` with note "snapshot, date unknown".
   Other stores → `prices_third_party` (seller, value, source, as_of). Leave empty when not found.
6. **Write pros/cons as short, original sentences** (they feed the draft script). Never paste review text.
7. Add `angle` (the everyday problem), `best_for`, `why_selected`, `callout` (on-screen feature, ≤ 26 chars),
   `shorts_hook`, and visual fields for prompts: `visual_description` (generic look, no brand),
   `broll_problem`, `broll_use`.
8. Rank 1..N (1 = best, shown last in the countdown). Put weaker-evidence items lower and say why.

## products.yaml format

```yaml
research:
  topic: "..."
  market: Amazon USA
  researched_on: 2026-11-03
  researcher: "Claude (web search) for Smart Finds Lab"
  method: "..."
  limitations: ["amazon.com could not be opened: no value verified", ...]
sources:
  AZ-X:   {url: "https://www.amazon.com/.../dp/B000000000", type: amazon_search_index,
           quality: "amazon (search index)", publisher: Amazon.com, title: "...", accessed: 2026-11-03}
  REV-X:  {url: "https://...", type: editorial_review, quality: "editorial (hands-on)", publisher: "...",
           title: "...", accessed: 2026-11-03}
products:
  - id: garlic-press            # short, stable id (used in scripts and file names)
    rank: 4                     # 99 for reserves
    status: shortlisted         # shortlisted | reserve | rejected
    category: Prep
    name:  {value: "OXO Good Grips Garlic Press", verified: false, sources: [AZ-X], as_of: 2026-11-03}
    short_name: "OXO Garlic Press"
    brand: {value: OXO, verified: false, sources: [AZ-X], as_of: 2026-11-03}
    asin:  {value: B00HEZ888K, verified: false, sources: [AZ-X], as_of: 2026-11-03, note: "from search result URL"}
    amazon_url: {value: "https://www.amazon.com/dp/B00HEZ888K", verified: false, sources: [AZ-X], as_of: 2026-11-03}
    price_amazon: {value: null, verified: false, sources: [], as_of: null, note: "not collected"}
    prices_third_party: [{value: 20.99, currency: USD, seller: "Macy's", source: REV-X, as_of: 2026-11-03}]
    rating_amazon: {value: 4.7, verified: false, sources: [REV-X], as_of: 2026-11-03, note: "as reported by ..."}
    review_count_amazon: {value: 35993, verified: false, sources: [REV-X], as_of: 2026-11-03}
    ratings_other: [{platform: Walmart, value: 4.6, count: 793, source: REV-Y, as_of: 2026-11-03}]
    features: [{text: "...", source: AZ-X}]
    pros: [{text: "...", source: REV-X}]
    cons: [{text: "...", source: REV-X}]
    best_for: "..."
    angle: "..."
    why_selected: "..."
    callout: "Built-in cleaner"
    shorts_hook: "..."
    visual_description: "a black metal garlic press with soft rubber handles"
    broll_problem: "..."
    broll_use: "..."
```

`source` types: amazon, owner_check (both can verify), amazon_search_index, manufacturer, editorial_review,
retailer, third_party. Run `studio.py research-report <slug>` — it must show 0 errors.

## Verification (owner)

`research/amazon-verification.csv` has one row per product with a link. The owner fills price, rating,
rating count, ASIN confirmation and the date checked, then `studio.py import-verification <slug>` marks
those fields `verified: true` with an `owner_check` source. Rows answered "no" for correct product /
available in US become `rejected` — promote a reserve (set its status + rank) and re-run research-report.
