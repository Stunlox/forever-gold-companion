# Data sources and intended use

## ForeverDB.net
We are requesting access to recipe, reagent, skill threshold, trainer source, item and vendor sell-price information. We intend to cache metadata locally and refresh approximately daily, subject to API rules. A visible attribution link to https://foreverdb.net will accompany its data in the app.

## Blizzard developer API
Intended for auction listings, quantities and buyout prices in the EU PvP Alliance market, subject to verification that the Forever endpoints are available. Price snapshots would be cached locally at an interval compliant with API rate limits.

## Quality and security
Data mapping, market identifiers, item variants, vendor values and recipe skill thresholds must be verified before production use. No API tokens, client secrets, or local databases should be committed. This is initially a personal non-commercial project, with a possible free community release later.
