"""Hero portrait loading, disk caching and image helpers."""

import io
from pathlib import Path
from typing import Optional, Tuple, Union

import requests
from PIL import Image, ImageDraw

from config import CACHE_DIR, HEADERS, ICON_SIZE


def get_cached_path(hero_id: int, variant: str = "") -> Path:
    """variant="" → head portrait, e.g. "smallmap" → <id>_smallmap.png"""
    suffix = f"_{variant}" if variant else ""
    return CACHE_DIR / f"{hero_id}{suffix}.png"


def download_image(
    url: str,
    size: Union[int, Tuple[int, int]] = ICON_SIZE,
    hero_id: Optional[int] = None,
    variant: str = "",
) -> Optional[Image.Image]:
    """
    Load a hero image.
    - If hero_id is given and a cached file exists → load from disk.
    - Otherwise download, save to cache (when hero_id given), then return.
    - `variant` keeps different image types (head / smallmap) in separate cache files.
    - `size` is a square side (int) or an explicit (width, height) tuple.
    """
    dims = (size, size) if isinstance(size, int) else tuple(size)

    # 1. Try cache first
    if hero_id is not None:
        cache_path = get_cached_path(hero_id, variant)
        if cache_path.exists():
            try:
                img = Image.open(cache_path).convert("RGBA")
                return img.resize(dims, Image.Resampling.LANCZOS)
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
                img.save(get_cached_path(hero_id, variant), "PNG")
            except Exception:
                pass

        return img.resize(dims, Image.Resampling.LANCZOS)
    except Exception:
        return None


def make_rounded(img: Image.Image, radius: int = 8) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out