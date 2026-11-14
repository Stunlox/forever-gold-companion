# Forever Gold Companion — Windows Community Build v0.3 (prototype)

A Windows desktop auction and profession research tool. **No Python installation is required by end users once the Windows installer has been built.**

## For players
Download `ForeverGoldCompanion_Setup_0.3.0.exe` from a successful GitHub Actions build (or a future GitHub Release), run the installer, and launch from Start Menu. Windows SmartScreen may warn about an unsigned community application; do not bypass security warnings unless you trust the source and have verified the release.

## For maintainers: building the installer
Upload these source files **including `.github/workflows/windows-release.yml`** to a GitHub repository. Open **Actions → Build Windows installer → Run workflow**. After the Windows job finishes, download the `ForeverGoldCompanion-Windows` artifact. The artifact contains a portable executable and a conventional installer. The GitHub-hosted Windows runner installs Python and packaging tools *during the build only*; players do not need them.

**Current status:** This is a build-ready source package, not an already compiled Windows installer. The CI build has not been executed or tested here.

## Included functionality
- Native desktop window (tkinter)
- Import actual auction listings and verified vendor prices from CSV
- Local SQLite history and vendor arbitrage scanner
- Hour-of-day observed listing price summary
- Profession route estimate and shopping list, when valid recipe data is supplied
- Experimental Blizzard/ForeverDB connectors (unverified)

## Important limitations
Live WoW Forever auction endpoints, market mapping, ForeverDB response format, trainer availability, vendor metadata, and skill-up probabilities are **not yet validated**. Never treat sample screenshots as live data. The profession engine is a preliminary expected-cost model, not a fully inventory-aware global optimiser. It requires data; it does not ship a verified Forever recipe database.

## Privacy and public distribution
**Do not embed a personal Blizzard Client Secret or ForeverDB API key in a public executable or repository.** Current connection fields accept credentials entered by the player at runtime; credentials are not persisted. A truly zero-configuration community release would require an approved, terms-compliant shared data service.

## Credits
Forever-specific recipe and item data is intended to be sourced from [ForeverDB.net](https://foreverdb.net), subject to their approval, availability, attribution and API rules. This project is unofficial and not endorsed by Blizzard.

## Testing
`python -m unittest discover -s tests -v` for maintainers. Windows UI and API integrations still need real-world testing.

## Installer note
The installer targets the current user’s LocalAppData Programs folder, avoiding administrator permissions. Windows binaries are produced by the GitHub Actions workflow, not included in this source archive.
