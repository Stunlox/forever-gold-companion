# Forever Gold Companion v0.6 — Data Diagnostics

This is a **Windows build source package**, not a compiled installer. Upload all extracted files to the repository, then run the existing **Build Windows installer** GitHub Actions workflow on `main`. Download the new run's artifact and install `ForeverGoldCompanion_Setup_0.6.0.exe`. Users do not need Python.

## Improvements
- Profession Planner displays saved recipe count for the selected profession, listing count for the selected AH ID, snapshot timestamp, and a specific next action.
- "Check data availability" refreshes those counts without needing to contact APIs.
- Calculation errors identify which dataset is missing.
- Discover AH IDs now opens a readable table with English names and a selectable ID instead of dumping raw API JSON into the status bar.
- All counts use the existing local SQLite database and selected auction house ID.

## Notes
- A successful API request does not guarantee useful recipes or auction listings were imported. Check the **counts**, not just the connection status.
- The ForeverDB API schema, profession coverage, and realm mappings remain unverified. The app does not manufacture missing data.
- Do not commit your Blizzard secret or ForeverDB API key.
- Run unit tests with `python -m unittest discover -s tests -v` (maintainers only).
