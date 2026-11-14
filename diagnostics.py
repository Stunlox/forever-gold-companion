"""Pure helpers for v0.6 data availability and auction house discovery."""

def planner_diagnostics(profession, house, recipe_count, listing_count, stamp):
    recipes = f"{profession.title()} recipes: {recipe_count:,}"
    auction = f"AH {house} listings: {listing_count:,}"
    snapshot = f"Snapshot: {stamp[:19].replace('T', ' ')} UTC" if stamp else "Snapshot: none"
    if not recipe_count and not listing_count:
        action = "Import recipes for the selected profession AND refresh the selected auction house."
    elif not recipe_count:
        action = "Missing profession recipes. Import them under Connections and verify the returned count."
    elif not listing_count:
        action = "Missing auction listings for this AH ID. Refresh this market under Connections."
    else:
        action = "Both datasets available. Ready to calculate (recipe coverage and material availability still matter)."
    return f"{recipes}  |  {auction}  |  {snapshot}\n{action}"

def format_auction_houses(records):
    result=[]
    for entry in records:
        if not isinstance(entry,dict):continue
        key=entry.get('key') or {}
        href=key.get('href','') if isinstance(key,dict) else ''
        name=entry.get('name') or {}
        if isinstance(name,dict):name=name.get('en_US') or name.get('en_GB') or next(iter(name.values()),'Unknown')
        ident=entry.get('id')
        if ident is None and href:
            import re
            match=re.search(r'/auctions/(\d+)',href)
            if match:ident=int(match.group(1))
        if ident is not None:result.append((str(ident),str(name),str(href)))
    return result
