# Forever Gold Companion

**Unofficial Windows desktop app prototype for World of Warcraft Forever.** Initially targeting **EU PvP Alliance**.

The goal is to calculate affordable profession levelling routes using Forever-specific standard-trainer recipes and auction prices, and to identify gold-making opportunities.

## Planned features
- Cheapest profession levelling route and consolidated material shopping list
- Historical auction prices, hourly and day-of-week market patterns
- Deals compared with historical prices and liquidity
- Vendor arbitrage (buyout below NPC sell price)
- Crafting profitability, watchlists, and CSV exports

## Technology
Planned: Python, PySide6, SQLite, and a standalone Windows executable.

## Status
**Early prototype.** Live API access, recipe coverage, auction-house IDs, vendor values and skill-up probabilities have not yet been validated. Demonstration prices are fictional.

## Data providers and attribution
We are seeking access to [ForeverDB.net](https://foreverdb.net) for Forever-specific recipes, reagent requirements, trainer availability, skill thresholds and item metadata. ForeverDB.net will be visibly credited with a clickable link wherever its data is displayed, subject to its API terms and approval.

We intend to use Blizzard's developer API for auction data **if Forever endpoints are verified and supported**. Credentials will remain on the user's PC and will not be committed to this repository.

This project is not affiliated with or endorsed by Blizzard Entertainment.

See [ROADMAP.md](ROADMAP.md) and [data sources](docs/DATA_SOURCES.md).

## License
No open-source license has been granted at this stage.
