# Product shortlist — 10 Kitchen Gadgets That Actually Make Life Easier

Research date: 2026-11-03 · Video type: **research_based** (research-based: no hands-on testing claims)

Ranked as a countdown: #10 is shown first, #1 last.

| Rank | Product | Brand | ASIN | Amazon price | Third-party price (date) | Reported Amazon rating | Verification |
|---|---|---|---|---|---|---|---|
| #1 | [OXO Good Grips Salad Spinner, Large (4.0)](https://www.amazon.com/dp/B077TV6BL3) | OXO | B077TV6BL3 | — (check on Amazon) | — | 4.7★ / 38,000 ratings (unverified) | 0/4 verified |
| #2 | [TempPro (ThermoPro) TP19H Instant Read Meat Thermometer](https://www.amazon.com/dp/B07XXSYLL8) | TempPro / ThermoPro | B07XXSYLL8 | — (check on Amazon) | — | — (on Walmart: 4.7★ / 3,488)  | 0/4 verified |
| #3 | [Fullstar The Original Pro Chopper, 4-in-1](https://www.amazon.com/dp/B0B8SQR665) | Fullstar | B0B8SQR665 | — (check on Amazon) | $39.99 list price per BestReviews (2026-11-03) | — (on Walmart: 4.6★ / 793)  | 0/4 verified |
| #4 | [OXO Good Grips Garlic Press (die-cast zinc)](https://www.amazon.com/dp/B00HEZ888K) | OXO | B00HEZ888K | $20.99 (snapshot, unverified) | $20.99 Macy's (sale) (2026-11-02) | 4.7★ / 35,993 ratings (unverified) | 0/4 verified |
| #5 | [Microplane Premium Classic Series Zester/Grater (46020)](https://www.amazon.com/dp/B00151WA06) | Microplane | B00151WA06 | — (check on Amazon) | $18.99 US retail listing (per search summary) (2026-11-03) | 4.8★ / 49,000 ratings (unverified) | 0/4 verified |
| #6 | [KitchenAid All Purpose Kitchen Shears with Protective Sheath](https://www.amazon.com/dp/B07TLNSW1S) | KitchenAid | B07TLNSW1S | 7.59-12.99 (varies by color) (snapshot, unverified) | $7.51 lowest of range on ShopSavvy ($7.51-$26.85) (2026-11-03) | 4.8★ / 71,000 ratings (unverified) | 0/4 verified |
| #7 | [Zulay Kitchen Metal 2-in-1 Lemon Lime Squeezer](https://www.amazon.com/dp/B00YBP918M) | Zulay Kitchen | B00YBP918M | — (check on Amazon) | — | 4.7★ / 47,137 ratings (unverified) | 0/4 verified |
| #8 | [Etekcity 0.1g Food Kitchen Scale with Bowl, 11 lb](https://www.amazon.com/dp/B08BPB9T1N) | Etekcity | B08BPB9T1N | — (check on Amazon) | $18.00 price named in Tom's Guide test (model match unconfirmed) (2026-11-03) | — (on Amazon (as reported by Product Review Crew, basic model): 4.1★ / 660)  | 0/4 verified |
| #9 | [Amazon Basics Silicone Baking Mat, 2-Pack (16.5 x 11.6 in)](https://www.amazon.com/dp/B0725GYNG6) | Amazon Basics | B0725GYNG6 | — (check on Amazon) | — | 4.7★ / 98,000 ratings (unverified) | 0/4 verified |
| #10 | [OXO Good Grips 3-in-1 Avocado Slicer (Green)](https://www.amazon.com/dp/B0088LR592) | OXO | B0088LR592 | — (check on Amazon) | $9.99 ShopSavvy listing (2026-11-03); $11.99 Bloomingdale's (2026-11-03) | — (on Bloomingdale's: 4.5★ / 107)  | 0/4 verified |

### Why this order

- **#1 OXO Good Grips Salad Spinner, Large (4.0)**: Most consistently recommended item in the research: named a top salad spinner by several outlets and reported at 4.7 stars from 38,000+ Amazon reviewers. Daily-use, very visual.
- **#2 TempPro (ThermoPro) TP19H Instant Read Meat Thermometer**: Solves a real food-safety problem; listing showed very high recent sales (search snapshot). Note: brand is moving from ThermoPro to TempPro, and buyers may receive either name.
- **#3 Fullstar The Original Pro Chopper, 4-in-1**: Hugely popular prep tool (search snapshot showed 10K+ bought in a month on a Fullstar listing) with clear before/after visuals. Honest con: cleaning.
- **#4 OXO Good Grips Garlic Press (die-cast zinc)**: Long-standing best seller with very high reported rating volume (4.7 from ~36K).
- **#5 Microplane Premium Classic Series Zester/Grater (46020)**: Classic, highly rated tool with strong visual payoff (fluffy parmesan, bright zest).
- **#6 KitchenAid All Purpose Kitchen Shears with Protective Sheath**: Cheap, extremely popular, many uses = easy 'why didn't I buy this sooner' moment.
- **#7 Zulay Kitchen Metal 2-in-1 Lemon Lime Squeezer**: Inexpensive, satisfying visual, very high reported rating volume. Note: a different Zulay listing (B072N94M7L) showed as unavailable, so this 2-in-1 listing was chosen.
- **#8 Etekcity 0.1g Food Kitchen Scale with Bowl, 11 lb**: Real accuracy benefit for bakers; weaker evidence than others (Etekcity models are often mixed up in reviews) - verify model and rating on Amazon.
- **#9 Amazon Basics Silicone Baking Mat, 2-Pack (16.5 x 11.6 in)**: Cheap, reusable, very high reported rating volume; good sustainability angle.
- **#10 OXO Good Grips 3-in-1 Avocado Slicer (Green)**: Safety angle + very visual. Lower rank: ratings found are from other retailers, and a test kitchen found its slicing only average.

### Reserves (can replace a product you reject)

- Basic Haus Reusable Silicone Stretch Lids, 7 Pack — Reserve: useful, but evidence is mostly generic brands and the seal is inconsistent per reviews.
- OXO Good Grips Little Salad & Herb Spinner — Reserve: swap in if you prefer a smaller spinner (search snapshot showed it as a #1 Best Seller).

## What you need to do

1. Open `research/amazon-verification.csv` (or the .md version) and check each product on Amazon.com: is it the right product, available in the US, and what are the **current** price, rating and number of ratings.
2. Fill in the columns, then run:

   `python scripts/studio.py import-verification kitchen-gadgets-10`

3. If you are happy with the products (you can approve before or after verifying), run:

   `python scripts/studio.py approve-products kitchen-gadgets-10`

Nothing that costs money (voice, video generation) happens before approval.
