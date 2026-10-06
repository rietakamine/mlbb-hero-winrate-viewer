"""Network calls to the Mobile Legends APIs."""

from typing import Dict, List

import requests

from config import HEADERS, HERO_API_URL, LANE_ORDER, TYPE_ORDER, WINLIST_API_URL

# Nested blocks that describe *other* heroes (counters, synergies...) and must
# not be mistaken for the hero's own fields.
_SKIP_KEYS = ("relation",)


def _collect(obj, key: str) -> list:
    """Recursively collect every value stored under `key` (skipping _SKIP_KEYS)."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _SKIP_KEYS:
                continue
            if k == key:
                found.append(v)
            else:
                found.extend(_collect(v, key))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_collect(item, key))
    return found


def _tidy(text: str, canonical) -> str:
    """Fix capitalization: known names map to their canonical form
    ("fighter" -> "Fighter", "exp lane" -> "EXP Lane"); otherwise each word
    gets an uppercase first letter and the rest is left alone."""
    key = text.casefold()
    for name in canonical:
        if name.casefold() == key:
            return name
    return " ".join(w[:1].upper() + w[1:] for w in text.split())


def _strings(values, canonical=()) -> List[str]:
    """Unique, non-empty, stripped (and capitalization-fixed) strings in original order."""
    out: List[str] = []
    for v in values:
        if isinstance(v, str):
            v = _tidy(v.strip(), canonical)
            if v and v not in out:
                out.append(v)
    return out


def _fix_url(url: str) -> str:
    return "https:" + url if url.startswith("//") else url


def fetch_all_heroes() -> Dict[int, dict]:
    """
    Return {hero_id: {"name", "head_big", "smallmap", "types", "lanes"}}.

    types = every `sort_title`  (e.g. Assassin, Marksman)
    lanes = every `road_sort_title` (e.g. Roam, Gold Lane)
    """
    payload = {
        "pageSize": 200,
        "pageIndex": 1,
        "filters": [],
        "sorts": [],
        "object": [],
    }
    resp = requests.post(HERO_API_URL, json=payload, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Hero API error: {data.get('message')}")

    result = {}
    for record in data.get("data", {}).get("records", []):
        try:
            d = record["data"]
            hid = int(d["hero_id"])
            hero_data = (d.get("hero") or {}).get("data") or {}
            name = hero_data["name"]

            head_big = d.get("head_big") or d.get("head") or ""
            smallmap = (
                hero_data.get("smallmap")
                or d.get("smallmap")
                or next(iter(_strings(_collect(d, "smallmap"))), "")
            )

            result[hid] = {
                "name": name,
                "head_big": _fix_url(head_big),
                "smallmap": _fix_url(smallmap),
                "types": _strings(_collect(d, "sort_title"), TYPE_ORDER),
                "lanes": _strings(_collect(d, "road_sort_title"), LANE_ORDER),
            }
        except (KeyError, TypeError, ValueError):
            continue
    return result


def fetch_player_winlist(uid: str) -> dict:
    """Return the raw win-list JSON for a player UID."""
    url = f"{WINLIST_API_URL}?uid={uid}"
    resp = requests.post(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"Winlist API error: {data.get('message')}")
    return data