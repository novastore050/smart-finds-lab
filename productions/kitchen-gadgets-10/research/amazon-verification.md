# Amazon verification sheet — 10 Kitchen Gadgets That Actually Make Life Easier

Open each link **on Amazon.com (USA)** and fill the matching row in `amazon-verification.csv` (Excel, Google Sheets or Numbers can open it; save it as CSV again). Rows are in countdown order.

Check: right product and model? · available in the US? · current price · star rating · number of ratings · ASIN (under 'Product information').

| Order | Rank | Product | Model | Amazon link | ASIN found | What to check |
|---|---|---|---|---|---|---|
| 1 | 10 | PowerLix Milk Frother Handheld with Stand (Deep Blue) | — | [open](https://www.amazon.com/dp/B08CVPQJHJ) | B08CVPQJHJ | pick ONE variant to link: ratings differ by colour/model; confirm stand is included |
| 2 | 9 | KitchenAid All Purpose Kitchen Shears with Protective Sheath, 8.72 Inch, Black | KE351OHOBA | [open](https://www.amazon.com/dp/B07PZF3QS3) | B07PZF3QS3 | ASIN changed to the black listing B07PZF3QS3 (B07TLNSW1S is Aqua Sky); model number differs between listings (KE351OHOBA vs KC351OHOBA); record the star rating |
| 3 | 8 | OXO Good Grips Garlic Press (die-cast zinc) | 11107400 | [open](https://www.amazon.com/dp/B00HEZ888K) | B00HEZ888K | record the Amazon star rating and count (not found directly); check colour (Black vs Silver) |
| 4 | 7 | Zulay Kitchen Metal 2-in-1 Lemon Lime Squeezer | — | [open](https://www.amazon.com/dp/B00YBP918M) | B00YBP918M | the rating count on Amazon (37,677) differs from a third-party figure (47,137) - record the live one |
| 5 | 6 | Original Scrub Daddy Sponge, 4 Count | — | [open](https://www.amazon.com/dp/B07ND5C1LW) | B07ND5C1LW | no Amazon rating found via search - record the rating on the 4-count listing; choose the pack size you want to link (1, 4 or 8 count) |
| 6 | 5 | Microplane Premium Classic Series Zester/Grater, Black | 46020 | [open](https://www.amazon.com/dp/B00151WA06) | B00151WA06 | each colour has its own model number - 46020 is black |
| 7 | 4 | Fullstar Pro Original Vegetable Chopper & Spiralizer (4-in-1) | TF1096C-8 | [open](https://www.amazon.com/dp/B0764HS4SL) | B0764HS4SL | ASIN changed to B0764HS4SL (the listing showing model TF1096C-8); confirm colour/blade count; Fullstar sells many similar versions (2-in-1 to 14-in-1) - make sure the link is the 4-in-1 |
| 8 | 3 | TempPro TempSwift TP19H Instant Read Meat Thermometer | TP19H | [open](https://www.amazon.com/dp/B07XXSYLL8) | B07XXSYLL8 | brand shows as TempPro (ThermoPro rebrand) - buyers may receive either name; check whether the 'newer version' should be featured instead |
| 9 | 2 | Dash Rapid Egg Cooker, 6 Egg Capacity, Black (DEC005BK) | DEC005BK | [open](https://www.amazon.com/dp/B00DDXWFY0) | B00DDXWFY0 | confirm the black DEC005BK listing is in stock (the white one was unavailable); Reviewed tested the 12-egg Deluxe version, not this exact model |
| 10 | 1 | OXO Good Grips Salad Spinner, 6.22 Qt | 32480 | [open](https://www.amazon.com/dp/B00004OCKR) | B00004OCKR | ASIN corrected to the classic 6.22 Qt listing B00004OCKR (was the green '4.0' variant B077TV6BL3); confirm rating/count on B00004OCKR itself |
| reserve | reserve | Etekcity 0.1g Food Kitchen Scale with Bowl, 11 lb | — | [open](https://www.amazon.com/dp/B08BPB9T1N) | B08BPB9T1N | — |
| reserve | reserve | Amazon Basics Silicone Baking Mat, 2-Pack (16.5 x 11.6 in) | — | [open](https://www.amazon.com/dp/B0725GYNG6) | B0725GYNG6 | — |
| reserve | reserve | Basic Haus Reusable Silicone Stretch Lids, 7 Pack | — | [open](https://www.amazon.com/dp/B0FGW5LZTX) | B0FGW5LZTX | — |
| reserve | reserve | Evo Oil Sprayer Bottle, 8-ounce, Set of 2 | — | [open](https://www.amazon.com/dp/B00ORXO9TO) | B00ORXO9TO | — |

When done:

```bash
python scripts/studio.py import-verification kitchen-gadgets-10
```
