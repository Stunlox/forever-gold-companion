# Forever Gold Companion v0.5 — Auction Browser

New dedicated Auction house browser with category and subcategory tabs, item search, sortable listing summary and CSV item catalogue import.

**Item catalogue CSV:** `item_id,name,category,subcategory`. Auction snapshots do not contain taxonomy or names, so unknown items appear as Uncategorised until imported. All item values reflect the local latest auction snapshot, not completed sales.

**Build:** upload all files to GitHub and trigger the Windows installer workflow on main. The workflow creates an EXE and Inno Setup installer; players do not need Python.

**Known limitations:** API mapping and item taxonomy source not independently validated. Browser shows up to 5,000 matching items and aggregates asking prices.
