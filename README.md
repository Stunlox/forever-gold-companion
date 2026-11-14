



WoW Forever Gold Companion

A powerful desktop application designed to help World of Warcraft Forever players maximise their gold, optimise profession levelling, and identify profitable auction house opportunities.

Overview

Forever Gold Companion is a free, non-commercial Windows application currently in development, initially focused on the EU PvP Alliance auction house.

The goal is to combine WoW Forever-specific profession data with auction house pricing and historical market trends to help players make smarter economic decisions.

Key Features

1. Profession Levelling Optimiser

- Calculate the cheapest route to level professions from 1–300.
- Use WoW Forever-specific recipes available from standard profession trainers.
- Compare material costs using auction house prices.
- Account for recipe difficulty and expected skill-up rates.
- Identify when crafting intermediate materials is cheaper than purchasing them.
- Generate complete shopping lists and crafting instructions.

2. Auction House Market Intelligence

- Track auction house prices over time.
- Analyse price fluctuations by hour and day of the week.
- Identify historically favourable buying and selling windows.
- Compare current prices against historical averages.
- Track market supply and price volatility.

3. Deal Sniper

- Identify items listed significantly below their typical market value.
- Calculate potential resale profits after auction house fees.
- Highlight profitable opportunities based on historical pricing.
- Monitor selected items for price drops.

4. Vendor Arbitrage

- Detect items listed below their NPC vendor sell price.
- Calculate potential guaranteed vendor resale margins, subject to item restrictions and verified vendor values.
- Highlight opportunities to purchase items cheaply and sell them directly to NPC vendors.

5. Crafting Profit Calculator

- Compare crafting material costs against finished item prices.
- Identify potentially profitable recipes.
- Account for intermediate crafting, auction house fees and estimated resale values.

6. Watchlists and Alerts

- Create personalised item watchlists.
- Set target purchase and selling prices.
- Receive desktop notifications when tracked opportunities are detected.

Technical Architecture

The application is being developed using:

- Python — Data collection and optimisation algorithms.
- PySide6 / Qt — Native Windows desktop interface.
- SQLite — Local storage of historical prices and recipe information.
- Blizzard API — Intended source of auction house data, subject to verification of WoW Forever support.
- ForeverDB API — Proposed source of WoW Forever-specific profession recipes, item information, reagents, skill thresholds and NPC vendor values, subject to API approval.

Data Sources and Attribution

This project intends to use data provided by "ForeverDB.net" (https://foreverdb.net), subject to approval and its API usage requirements.

ForeverDB will receive visible attribution within the application, including a clickable link wherever its data is displayed.

Recipe and item metadata will be cached locally to reduce unnecessary API requests. Refresh intervals will respect provider rate limits and usage policies.

Auction house data will be collected separately, where supported, and stored locally for historical analysis.

Development Status

Early development / prototype stage.

The desktop interface and calculation engine are being prototyped. Live API integrations, recipe accuracy and market calculations still require validation.

Future plans include releasing a standalone Windows executable and potentially making the application available to the wider WoW Forever community.

Disclaimer

Forever Gold Companion is an independent, unofficial community project and is not affiliated with or endorsed by Blizzard Entertainment.

World of Warcraft and associated trademarks belong to their respective owners.

This project is intended for personal, non-commercial use during initial development.

