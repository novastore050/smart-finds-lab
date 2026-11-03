# Script guide (stage 5)

`studio.py draft-script <slug>` builds `script/script.yaml` from approved research. It is a factual
skeleton — **rewrite the narration** so it sounds natural, original and human, then run
`studio.py check-script <slug>` until it reports no errors. `script/script.md` is the readable version.

## Structure (long-form, countdown)

| Scene | Role | Length | Content |
|---|---|---|---|
| s01 | hook | 8–15 s | The everyday frustration + promise + reason to stay to #1. No brand names yet. |
| (auto) | intro card | 2.6 s | Inserted by the editor after the hook. |
| s02… | product | 25–45 s | "Number N: <short name>." problem → what it does → what buyers like → one honest downside → who it's for. |
| last | wrapup | 8–15 s | Prices change → links in description → question for comments → subscribe. |
| (auto) | outro | 12 s | End-screen card. |

US audience: plain, friendly American English, short sentences (~12–15 words), talk to "you",
~150–160 words per minute. Use "buyers say", "reviewers point out", "on paper", "according to the specs".

## Honesty rules (enforced by check-script)

- `video_type: research_based` (default): no testing claims ("I tested", "we tested", "after using it",
  "I bought", "hands-on", "in my tests"…).
- `hands_on` videos: every product scene needs `hands_on: {tested_by: "...", date: YYYY-MM-DD, notes: "..."}`
  describing the real test. Only use when the owner actually tested the product.
- No prices or "$" in narration. Say "check the link for today's price".
- Star ratings / rating counts only if the research field is verified; add them to the scene's `claims`:
  `claims: [{text: "<exact sentence>", fields: [<product-id>.rating_amazon, <product-id>.review_count_amazon]}]`.
- Originality: any 7-word sequence matching a reference transcript is an error — rewrite it.

## Scene format

```yaml
- id: s03
  role: product            # hook | product | wrapup
  product: garlic-press    # research product id
  rank: 4
  basis: research_based
  narration: "Number four: the OXO Garlic Press. ..."
  on_screen: {badge: "#4", lower_third: "OXO Garlic Press", lower_third_sub: "Best for: ...", callout: "Built-in cleaner"}
  claims: []
  shots:
    - {id: s03-a, type: ai_broll, aspect: "16:9", product: garlic-press, prompt: "the problem moment ..."}
    - {id: s03-b, type: ai_broll, aspect: "16:9", product: garlic-press, prompt: "generic use ..."}
    - {id: s03-photo, type: product_photo, product: garlic-press, file: assets/images/<slug>/garlic-press.jpg}
```

Shorts (3): `shorts: [{id: short1, product: <id>, use_scenes: [s11], hook: "...", title: "..."}]` —
usually the top 3 products. Each Short should be 20–60 s; if a product scene is shorter than ~20 s,
write a dedicated Short scene or lengthen the narration.
