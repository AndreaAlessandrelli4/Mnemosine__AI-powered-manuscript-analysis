"""
Image utilities — loading, compression, sorting by page number.

Improvement over notebooks:
- The notebooks hardcoded .jpg only; we support jpg/png/tiff/webp.
- The notebooks sorted alphabetically; we parse 3-digit prefix for correct order.
- compress_for_vl is cleaner: returns PIL Image directly, not base64 + raw bytes.
"""

from __future__ import annotations

import io
import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp"}

# Pattern: 3-digit prefix at start of filename (e.g., 001_nome.jpg)
PAGE_NUMBER_RE = re.compile(r"^(\d{3})")


def parse_page_number(filename: str) -> int:
    """
    Extract the 3-digit page number from filename prefix.
    Returns -1 if no match (file will sort first).
    """
    match = PAGE_NUMBER_RE.match(filename)
    if match:
        return int(match.group(1))
    return -1


def list_images(directory: str | Path) -> List[Tuple[int, str]]:
    """
    List supported image files in *directory*, sorted by page number.
    Returns list of (page_number, filename) tuples.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []

    results: List[Tuple[int, str]] = []
    for entry in os.listdir(directory):
        ext = Path(entry).suffix.lower()
        if ext in SUPPORTED_EXTENSIONS:
            page_num = parse_page_number(entry)
            results.append((page_num, entry))

    results.sort(key=lambda x: x[0])
    return results


def load_image(path: str | Path) -> Optional[Image.Image]:
    """Load an image and convert to RGB.  Returns None on failure."""
    try:
        img = Image.open(path).convert("RGB")
        return img
    except Exception as exc:
        logger.warning("Failed to open image %s: %s", path, exc)
        return None


def compress_for_vl(
    image_path: str | Path,
    max_bytes: int = 10_000_000,
) -> Optional[Image.Image]:
    """
    Load an image, compress to JPEG if oversized, return as PIL Image.
    Always converts to RGB first.
    """
    img = load_image(image_path)
    if img is None:
        return None

    # Check raw size by encoding to JPEG
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    if buf.tell() <= max_bytes:
        return img

    # Compress iteratively
    quality = 90
    while quality >= 20:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True, subsampling=2)
        if buf.tell() <= max_bytes:
            return Image.open(io.BytesIO(buf.getvalue()))
        quality -= 10

    # Last resort
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=20, optimize=True, subsampling=2)
    return Image.open(io.BytesIO(buf.getvalue()))


def image_to_base64(image_path: str | Path) -> str:
    """Read an image file and return base64 string for OpenAI API."""
    import base64

    path = Path(image_path)
    img = load_image(path)
    if img is None:
        raise ValueError(f"Cannot load image: {path}")

    buf = io.BytesIO()
    # Always send as JPEG for consistency + smaller size
    img.save(buf, format="JPEG", quality=90, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
