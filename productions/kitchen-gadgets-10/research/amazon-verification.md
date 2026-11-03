# Amazon verification sheet — 10 Kitchen Gadgets That Actually Make Life Easier

Open each link **on Amazon.com (USA)** and fill the matching row in `amazon-verification.csv` (Excel, Google Sheets or Numbers can open it; save it as CSV again). Rows are in countdown order.

Check: right product and model? · available in the US? · current price · star rating · number of ratings · ASIN (under 'Product information').

| Order | Rank | Product | Model | Amazon link | ASIN found | What to check |
|---|---|---|---|---|---|---|
| 1 | 10 | Zulay Kitchen Metal 2-in-1 Lemon Lime Squeezer | — | [open](https://www.amazon.com/dp/B00YBP918M) | B00YBP918M | the rating count on Amazon (37,677) differs from a third-party figure (47,137) - record the live one |
| 2 | 9 | KitchenAid All Purpose Kitchen Shears with Protective Sheath, 8.72 Inch, Black | KE351OHOBA | [open](https://www.amazon.com/dp/B07PZF3QS3) | B07PZF3QS3 | confirm the listing shows model KE351OHOBA; record the Amazon.com rating (only Australia/Singapore figures found for this ASIN) |
| 3 | 8 | Microplane Premium Classic Series Zester/Grater, Black | 46020 | [open](https://www.amazon.com/dp/B00151WA06) | B00151WA06 | each colour has its own model number - 46020 is black |
| 4 | 7 | OXO Good Grips Soap Dispensing Dish Brush with Handle | — | [open](https://www.amazon.com/dp/B0BK2R8TQB) | B0BK2R8TQB | confirm B0BK2R8TQB is the single brush (not a 2-pack or the palm brush); record the Amazon.com rating (only Singapore/Canada figures found) |
| 5 | 6 | PowerLix Milk Frother Handheld with Stainless Steel Stand - Deep Blue | — | [open](https://www.amazon.com/dp/B08CVPQJHJ) | B08CVPQJHJ | confirm B08CVPQJHJ opens the Deep Blue colour with the stand; record the rating shown on that page |
| 6 | 5 | Fullstar Pro Original Vegetable Chopper & Spiralizer (4-in-1) | TF1096C-8 | [open](https://www.amazon.com/dp/B0764HS4SL) | B0764HS4SL | ASIN changed to B0764HS4SL (the listing showing model TF1096C-8); confirm colour/blade count; Fullstar sells many similar versions (2-in-1 to 14-in-1) - make sure the link is the 4-in-1 |
| 7 | 4 | OXO Good Grips Salad Spinner, 6.22 Qt | 32480 | [open](https://www.amazon.com/dp/B00004OCKR) | B00004OCKR | record the Amazon.com star rating and count for B00004OCKR (only non-US Amazon figures found); confirm size (6.22 Qt) and model on the listing |
| 8 | 3 | TempPro TempSwift TP19H Instant Read Meat Thermometer | TP19H | [open](https://www.amazon.com/dp/B07XXSYLL8) | B07XXSYLL8 | brand shows as TempPro (ThermoPro rebrand); manufacturer page calls it 'TempSwift PLUS TP19H'; check whether the 'newer version' should be featured instead |
| 9 | 2 | Rubbermaid Brilliance Leak-Proof Food Storage Containers with Airtight Lids, Set of 3 (6 Pieces Total) | 2025903 | [open](https://www.amazon.com/dp/B01JCNEJSO) | B01JCNEJSO | record the live rating count (Amazon.com page showed 1,900 vs 83,371 on Amazon Singapore); confirm it is the 3-container / 6-piece set |
| 10 | 1 | Dash Rapid Egg Cooker, 6 Egg Capacity, Black (DEC005BK) | DEC005BK | [open](https://www.amazon.com/dp/B00DDXWFY0) | B00DDXWFY0 | confirm the black DEC005BK listing is in stock (the white one was unavailable); Reviewed tested the 12-egg Deluxe version, not this exact model |
| reserve | reserve | Original Scrub Daddy Sponge, 4 Count | — | [open](https://www.amazon.com/dp/B07ND5C1LW) | B07ND5C1LW | no Amazon rating found via search - record the rating on the 4-count listing; choose the pack size you want to link (1, 4 or 8 count) |
| reserve | reserve | Etekcity 0.1g Food Kitchen Scale with Bowl, 11 lb | — | [open](https://www.amazon.com/dp/B08BPB9T1N) | B08BPB9T1N | — |
| reserve | reserve | Amazon Basics Silicone Baking Mat, 2-Pack (16.5 x 11.6 in) | — | [open](https://www.amazon.com/dp/B0725GYNG6) | B0725GYNG6 | — |
| reserve | reserve | Basic Haus Reusable Silicone Stretch Lids, 7 Pack | — | [open](https://www.amazon.com/dp/B0FGW5LZTX) | B0FGW5LZTX | — |
| reserve | reserve | Evo Oil Sprayer Bottle, 8-ounce, Set of 2 | — | [open](https://www.amazon.com/dp/B00ORXO9TO) | B00ORXO9TO | — |
| reserve | reserve | Kuhn Rikon garlic press (listing B0000CD0HX) | 2315 | [open](https://www.amazon.com/dp/B0000CD0HX) | B0000CD0HX | — |

When done:

```bash
python scripts/studio.py import-verification kitchen-gadgets-10
```
