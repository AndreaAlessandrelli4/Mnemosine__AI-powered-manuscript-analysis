"""
Centralized configuration for Mnemosine backend.

All settings are read from environment variables (via .env file).
Fallbacks are defined here — do NOT hardcode values elsewhere.
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


# ── Enums ──────────────────────────────────────────────

class InferenceProvider(str, Enum):
    HF = "hf"
    OPENAI = "openai"


class DeviceType(str, Enum):
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"


# ── Settings ───────────────────────────────────────────

class Settings(BaseSettings):
    """Application settings loaded from .env with sensible defaults."""

    # -- Inference provider --
    inference_provider: InferenceProvider = Field(
        default=InferenceProvider.OPENAI,
        alias="INFERENCE_PROVIDER",
        description="Default inference provider: 'hf' (local) or 'openai' (API).",
    )

    # -- OpenAI --
    openai_api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY",
        description="OpenAI API key (never logged).",
    )
    openai_base_url: Optional[str] = Field(
        default=None,
        alias="OPENAI_BASE_URL",
        description="Optional custom base URL for OpenAI-compatible endpoints.",
    )
    openai_vision_model: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_VISION_MODEL",
        description="OpenAI model for vision tasks. Fallback: gpt-4o-mini.",
    )
    openai_text_model: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_TEXT_MODEL",
        description="OpenAI model for text tasks. Fallback: gpt-4o-mini.",
    )
    openai_temperature: float = Field(
        default=0.2,
        alias="OPENAI_TEMPERATURE",
        description="Sampling temperature for OpenAI calls.",
    )
    openai_max_output_tokens: int = Field(
        default=1200,
        alias="OPENAI_MAX_OUTPUT_TOKENS",
        description="Max tokens for OpenAI responses.",
    )

    # -- Manuscripts --
    manuscripts_root: str = Field(
        default="./manuscripts",
        alias="MANUSCRIPTS_ROOT",
        description="Root directory containing manuscript folders.",
    )

    # -- Prompts --
    prompt_dir: str = Field(
        default="../prompt",
        alias="PROMPT_DIR",
        description="Directory containing prompt .txt files.",
    )

    # -- Server --
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # -- Allowed devices --
    allowed_devices: str = Field(
        default="auto,cpu,cuda,mps",
        alias="ALLOWED_DEVICES",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "populate_by_name": True,
    }


# ── Device Detection ──────────────────────────────────

def detect_device() -> DeviceType:
    """Detect the best available compute device."""
    try:
        import torch

        if torch.cuda.is_available():
            return DeviceType.CUDA
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return DeviceType.MPS
    except ImportError:
        pass
    return DeviceType.CPU


def resolve_device(requested: DeviceType) -> DeviceType:
    """
    Resolve a requested device to an actual device.
    'auto' → best available; 'cuda' on Mac without CUDA → fallback to MPS if available.
    """
    if requested == DeviceType.AUTO:
        return detect_device()

    if requested == DeviceType.CUDA:
        try:
            import torch
            if torch.cuda.is_available():
                return DeviceType.CUDA
            # Fallback to MPS on Mac
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return DeviceType.MPS
        except ImportError:
            pass
        return DeviceType.CPU

    if requested == DeviceType.MPS:
        try:
            import torch
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return DeviceType.MPS
        except ImportError:
            pass
        return DeviceType.CPU

    return DeviceType.CPU


def has_gpu() -> bool:
    """Check if any GPU is available (CUDA or MPS)."""
    detected = detect_device()
    return detected in (DeviceType.CUDA, DeviceType.MPS)


@lru_cache()
def get_settings() -> Settings:
    """
    Return cached application settings.

    IMPORTANT: We use python-dotenv with override=True so that values
    in the project's .env file ALWAYS win over system environment
    variables.  This prevents stale keys set in ~/.zshrc, conda, etc.
    from silently overriding the project config.
    """
    from dotenv import load_dotenv

    # Look for .env in multiple locations (closest wins)
    env_paths = [
        Path.cwd() / ".env",                                        # backend/
        Path(__file__).resolve().parent.parent / ".env",             # backend/
        Path(__file__).resolve().parent.parent.parent / ".env",      # mnemosine/
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]
    env_file = None
    for p in env_paths:
        if p.exists():
            env_file = str(p)
            break

    if env_file:
        # override=True → .env values win over system env vars
        load_dotenv(env_file, override=True)
        return Settings(_env_file=env_file)
    return Settings()
