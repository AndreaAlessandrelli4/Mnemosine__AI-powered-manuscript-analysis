"""
Prompt loader — reads prompt .txt files from the configured prompt directory.
Caches content in memory after first read.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


@lru_cache(maxsize=16)
def load_prompt(prompt_path: str | Path) -> str:
    """
    Read a prompt file and return its content as string.
    Raises FileNotFoundError if the file does not exist.
    """
    path = Path(prompt_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    content = path.read_text(encoding="utf-8").strip()
    logger.info("Loaded prompt from %s (%d chars)", path.name, len(content))
    return content


def resolve_prompt_path(prompt_dir: str | Path, filename: str) -> Path:
    """Resolve a prompt filename relative to the prompt directory."""
    return Path(prompt_dir).resolve() / filename


def get_metadata_prompt(prompt_dir: str | Path) -> str:
    return load_prompt(resolve_prompt_path(prompt_dir, "prompt_metadati.txt"))


def get_transcription_prompt(prompt_dir: str | Path) -> str:
    return load_prompt(resolve_prompt_path(prompt_dir, "prompt_trascrizione.txt"))


def get_aggregation_prompt(prompt_dir: str | Path) -> str:
    return load_prompt(resolve_prompt_path(prompt_dir, "prompt_aggregation_metadati.txt"))
