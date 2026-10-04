"""App-wide constants: API endpoints, request headers, cache location."""

from pathlib import Path

# --- API ---------------------------------------------------------------
HERO_API_URL = "https://api.gms.moontontech.com/api/gms/source/2669606/2756564"
WINLIST_API_URL = "https://mlapi.mobilelegends.com/mlAPI/GetHeroWinList.php"

# pvptype values returned by the win-list API
PVP_CLASSIC = "1"
PVP_RANK = "2"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
}

# --- Images / cache ----------------------------------------------------
ICON_SIZE = 84  # grid portrait size in px

# Cache directory for hero icons (next to main.py)
CACHE_DIR = Path(__file__).resolve().parent / "cache" / "icons"
