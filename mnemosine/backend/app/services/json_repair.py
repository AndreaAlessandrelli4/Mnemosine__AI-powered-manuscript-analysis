"""
Conservative JSON repair.

The VL model sometimes returns JSON with minor issues:
- Wrapped in markdown fences (```json ... ```)
- Trailing commas
- Single-quoted strings (rare)

This module tries to fix those issues without altering valid content.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def repair_json(raw: str) -> str:
    """
    Attempt conservative repair and return a valid JSON string.
    Raises ValueError if repair fails.
    """
    cleaned = raw.strip()

    # 1) Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # 2) Try parsing as-is first
    try:
        obj = json.loads(cleaned)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        pass

    # 3) Remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # 4) Try again
    try:
        obj = json.loads(cleaned)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        pass

    # 5) Try to find the first { and last } (extract JSON object)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        subset = cleaned[start : end + 1]
        # Remove trailing commas again
        subset = re.sub(r",\s*([}\]])", r"\1", subset)
        try:
            obj = json.loads(subset)
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Unable to repair JSON. Raw text (first 200 chars): {raw[:200]}")


def try_parse_json(raw: str) -> Optional[Any]:
    """
    Try to parse raw text as JSON (with repair).
    Returns the parsed object or None.
    """
    try:
        repaired = repair_json(raw)
        return json.loads(repaired)
    except (ValueError, json.JSONDecodeError):
        return None


def ensure_json_string(raw: str) -> str:
    """
    Return a well-indented JSON string, applying repair if needed.
    Raises ValueError on complete failure.
    """
    return repair_json(raw)
