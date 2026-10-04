"""Pure data helpers: parsing the win-list response and computing winrates."""

from config import PVP_CLASSIC, PVP_RANK


def parse_winlist(raw: dict):
    """Split the raw response into (classic, rank) dicts of {hero_id: (total, wins)}."""
    classic, rank = {}, {}
    for block in raw.get("data", []):
        pvp = str(block.get("pvptype", ""))
        target = classic if pvp == PVP_CLASSIC else rank if pvp == PVP_RANK else None
        if target is None:
            continue
        for h in block.get("herodata", []):
            try:
                hid = int(h["id"])
                total = int(h["total"])
                wins = int(h["win"])
                if total > 0:
                    target[hid] = (total, wins)
            except (KeyError, TypeError, ValueError):
                continue
    return classic, rank


def calc_wr(total: int, wins: int) -> float:
    """Winrate as a percentage rounded to 1 decimal."""
    return round((wins / total) * 100, 1) if total > 0 else 0.0
