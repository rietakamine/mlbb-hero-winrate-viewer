"""Hero portrait loading, disk caching and image helpers."""

import io
from pathlib import Path
from typing import Optional

import requests
from PIL import Image, ImageDraw

from config import CACHE_DIR, HEADERS, ICON_SIZE


def get_cached_path(hero_id: int) -> Path:
    return CACHE_DIR / f"{hero_id}.png"


def download_image(url: str, size: int = ICON_SIZE, hero_id: Optional[int] = None) -> Optional[Image.Image]:
    """
    Load hero portrait.
    - If hero_id is given and a cached file exists → load from disk.
    - Otherwise download, save to cache (when hero_id given), then return.
    """
    # 1. Try cache first
    if hero_id is not None:
        cache_path = get_cached_path(hero_id)
        if cache_path.exists():
            try:
                img = Image.open(cache_path).convert("RGBA")
                return img.resize((size, size), Image.Resampling.LANCZOS)
            except Exception:
                pass  # corrupted cache → re-download

    if not url:
        return None

    # 2. Download
    try:
        resp = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=10)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")

        # 3. Save original (full-res) to cache
        if hero_id is not None:
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                img.save(get_cached_path(hero_id), "PNG")
            except Exception:
                pass

        return img.resize((size, size), Image.Resampling.LANCZOS)
    except Exception:
        return None


def make_rounded(img: Image.Image, radius: int = 8) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out
