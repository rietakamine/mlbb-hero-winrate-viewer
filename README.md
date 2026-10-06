# MLBB Hero Winrate Viewer

A free, open-source desktop app (Tkinter) that shows a Mobile Legends: Bang Bang player's hero winrates in a dark, ImGui-inspired UI.

> **Unofficial fan project.** Not affiliated with, endorsed by, or sponsored by Moonton. See [Disclaimer](#disclaimer).

- Enter a player **UID** and fetch their stats
- See a grid of hero portraits, sorted by most-played
- Each card shows the combined winrate and total matches
- **Filter** by hero type (Assassin, Marksman, ...) and by lane (Roam, Gold Lane, ...)
- **Sort** by most played, winrate, or name
- The grid **adapts to the window size**: columns are added or removed as you resize
- Click a hero to open a popup with the hero's `smallmap` image, type/lane, and **Classic**, **Rank**, and **Combined** stats (wins / total → winrate)
- Hero portraits are cached on disk so later launches are faster

## Requirements

- Python 3.9+
- Tkinter (bundled with the standard Windows/macOS Python installers; on Debian/Ubuntu: `sudo apt install python3-tk`)
- Packages in `requirements.txt` (`requests`, `Pillow`)

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
python main.py
```

1. Wait for the status bar to say the heroes are ready.
2. Type a numeric player UID and press **Enter** or click **Fetch**.
3. Click any portrait for the detailed Classic / Rank / Combined breakdown.

## Project structure

```
.
├── main.py            # Entry point
├── config.py          # API URLs, headers, pvp type IDs, cache path, icon sizes
├── api.py             # Network calls (hero list, player win list)
├── stats.py           # Win list parsing + winrate calculation (no UI/network)
├── images.py          # Image download, disk cache (head + smallmap), rounded corners
├── requirements.txt
├── LICENSE
├── README.md
└── ui/
    ├── theme.py       # Color palette and card spacing
    ├── scrollbar.py   # ThinScrollbar widget
    ├── filter_bar.py  # FilterBar + ChipRow (type / lane filters, sort)
    ├── hero_card.py   # HeroCard widget (one grid cell)
    ├── popup.py       # StatsPopup window
    └── app.py         # Main App window, wiring everything together
```

Dependency direction is one-way: `ui/*` → `api` / `stats` / `images` → `config`. The non-UI modules never import Tkinter, so they're easy to test or reuse.

## How it works

1. On startup, `api.fetch_all_heroes()` loads hero names, portrait URLs (`head_big`, `smallmap`), types (`sort_title`) and lanes (`road_sort_title`) in a background thread. The filter chips are built from whatever types and lanes the API returns.
2. On **Fetch**, `api.fetch_player_winlist(uid)` gets the player's raw stats and `stats.parse_winlist()` splits them into Classic and Rank dictionaries of `{hero_id: (total, wins)}`.
3. Portraits are loaded in parallel (12 worker threads) through `images.download_image()`, which checks `cache/icons/` first and only downloads on a miss.
4. Every hero card is created once. Filtering and sorting only hide/re-grid the existing cards, and a resize recomputes the column count from the window width.
5. Clicking a card downloads (or loads from cache) the hero's `smallmap` image for the popup, falling back to the portrait if there isn't one.
6. The UI is updated from worker threads only via `self.after(0, ...)`, keeping Tkinter calls on the main thread.

## Configuration

Edit `config.py` for API endpoints, request headers, `ICON_SIZE` (grid) and `POPUP_ICON_SIZE` (popup), and `ui/theme.py` for colors and card spacing (`CARD_PAD`). The column count is automatic. Chip order for types and lanes lives in `ui/filter_bar.py` (`TYPE_ORDER`, `LANE_ORDER`).

## Cache

Images are saved next to `main.py` as `cache/icons/<hero_id>.png` (portrait) and `cache/icons/<hero_id>_smallmap.png` (popup image). Delete the folder to force a re-download.

## Notes

- The app uses unofficial, undocumented Mobile Legends endpoints. They can change or stop working at any time, and rate limits may apply.
- Winrates are only shown for heroes with at least one recorded match.
- The UI uses Windows fonts (Segoe UI, Consolas). Other platforms will fall back to a default font, and mouse-wheel scrolling is tuned for Windows/macOS delta values.

## Disclaimer

This project is an unofficial, non-commercial fan tool and is **not affiliated with, endorsed by, or sponsored by Moonton** or Mobile Legends: Bang Bang.

- The APIs, hero data, names, and portrait images used by this app are owned by **Moonton / Mobile Legends: Bang Bang** and remain their property. *Mobile Legends* and *Mobile Legends: Bang Bang* are trademarks of Moonton.
- This repository does not claim ownership of any of that content and does not redistribute it. Portraits are downloaded on demand and cached locally on your own machine.
- The endpoints are not an official public API. Use of them is subject to Moonton's terms, and they may change, be rate-limited, or be shut down at any time.
- You use this software **at your own risk**. The author is not responsible for any consequences of its use, including data errors, broken endpoints, or any action taken against your account or IP.
- If you are a rights holder and want something changed or removed, please open an issue.

## License

The source code in this repository is released under the [MIT License](LICENSE): free to use, copy, modify, and distribute, provided "as is" with no warranty.

The MIT License covers only the code in this repository. It does not grant any rights to Moonton's APIs, data, names, or images.
