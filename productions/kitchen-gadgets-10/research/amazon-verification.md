# Amazon verification sheet — 10 Kitchen Gadgets That Actually Make Life Easier

Open each link **on Amazon.com (USA)** and fill the matching row in `amazon-verification.csv` (Excel, Google Sheets or Numbers can open it; save it as CSV again).

Check: right product? · available in the US? · current price · star rating · number of ratings · ASIN (shown under 'Product information' on the page).

| # | Product | Amazon link | ASIN found | Third-party price (reference only) |
|---|---|---|---|---|
| 1 | OXO Good Grips Salad Spinner, Large (4.0) | [open](https://www.amazon.com/dp/B077TV6BL3) | B077TV6BL3 | — |
| 2 | TempPro (ThermoPro) TP19H Instant Read Meat Thermometer | [open](https://www.amazon.com/dp/B07XXSYLL8) | B07XXSYLL8 | — |
| 3 | Fullstar The Original Pro Chopper, 4-in-1 | [open](https://www.amazon.com/dp/B0B8SQR665) | B0B8SQR665 | $39.99 list price per BestReviews (2026-11-03) |
| 4 | OXO Good Grips Garlic Press (die-cast zinc) | [open](https://www.amazon.com/dp/B00HEZ888K) | B00HEZ888K | $20.99 Macy's (sale) (2026-11-02) |
| 5 | Microplane Premium Classic Series Zester/Grater (46020) | [open](https://www.amazon.com/dp/B00151WA06) | B00151WA06 | $18.99 US retail listing (per search summary) (2026-11-03) |
| 6 | KitchenAid All Purpose Kitchen Shears with Protective Sheath | [open](https://www.amazon.com/dp/B07TLNSW1S) | B07TLNSW1S | $7.51 lowest of range on ShopSavvy ($7.51-$26.85) (2026-11-03) |
| 7 | Zulay Kitchen Metal 2-in-1 Lemon Lime Squeezer | [open](https://www.amazon.com/dp/B00YBP918M) | B00YBP918M | — |
| 8 | Etekcity 0.1g Food Kitchen Scale with Bowl, 11 lb | [open](https://www.amazon.com/dp/B08BPB9T1N) | B08BPB9T1N | $18.00 price named in Tom's Guide test (model match unconfirmed) (2026-11-03) |
| 9 | Amazon Basics Silicone Baking Mat, 2-Pack (16.5 x 11.6 in) | [open](https://www.amazon.com/dp/B0725GYNG6) | B0725GYNG6 | — |
| 10 | OXO Good Grips 3-in-1 Avocado Slicer (Green) | [open](https://www.amazon.com/dp/B0088LR592) | B0088LR592 | $9.99 ShopSavvy listing (2026-11-03); $11.99 Bloomingdale's (2026-11-03) |
| reserve | Basic Haus Reusable Silicone Stretch Lids, 7 Pack | [open](https://www.amazon.com/dp/B0FGW5LZTX) | B0FGW5LZTX | — |
| reserve | OXO Good Grips Little Salad & Herb Spinner | [open](https://www.amazon.com/dp/B00005QB5U) | B00005QB5U | — |

When done:

```bash
python scripts/studio.py import-verification kitchen-gadgets-10
```

*Links without an ASIN are Amazon searches: pick the exact product and paste its URL in `amazon_url_if_different`.*
