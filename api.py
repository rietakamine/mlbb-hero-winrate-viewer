"""Network calls to the Mobile Legends APIs."""

from typing import Dict

import requests

from config import HEADERS, HERO_API_URL, WINLIST_API_URL


def fetch_all_heroes() -> Dict[int, dict]:
    """Return {hero_id: {"name": str, "head_big": str}} for every hero."""
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
            name = d["hero"]["data"]["name"]
            head_big = d.get("head_big") or d.get("head") or ""
            result[hid] = {"name": name, "head_big": head_big}
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
