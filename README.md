# Forever Gold Companion v0.4 — Dark Trading Terminal

A PySide6 desktop redesign of Forever Gold Companion for Windows. This is a **prototype** with a dark trading-terminal interface, left navigation, market overview, profession planner, vendor scanner, price history and experimental data connections.

## Community Windows installer (no Python needed for players)

Upload the contents of this archive to the GitHub repository, including `.github/workflows/windows-release.yml`. Run **Actions → Build Windows installer → Run workflow**. Once green, download the `ForeverGoldCompanion-Windows` artifact, extract it and run `ForeverGoldCompanion_Setup_0.4.0.exe`. Python and PySide6 are bundled by PyInstaller on GitHub's Windows build machine. No Python installation is needed by players.

**Do not upload this ZIP as a single file**; extract and upload its contents while retaining the directory structure. Replace old files when GitHub asks.

## Maintainer testing

`python -m unittest discover -s tests -v`

`python desktop.py` (requires dependencies installed)

## Current limitations

The Windows GUI has not been visually tested on a Windows machine in this environment. The Forever-specific Blizzard/ForeverDB API paths and data formats remain **unverified**. This app does not ship with real AH prices, verified profession recipe coverage, or a public zero-config API backend. Do not bundle personal API secrets. The optimizer is an expected-cost model and cannot guarantee skill-ups or exact shopping costs. Auction listings are not actual sales.

The app stores local SQLite data in `%USERPROFILE%\ForeverGoldCompanion\market.sqlite3`; it does not persist entered API credentials.

Unofficial community project, not affiliated with Blizzard or ForeverDB.
