"""
Abstract base class for inference providers.
Providers must implement run_vl() and run_text().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from PIL import Image


class InferenceProvider(ABC):
    """Base interface for VL and text inference."""

    @abstractmethod
    def run_vl(self, image_path: str | Path, prompt_text: str) -> str:
        """
        Run vision-language inference on a single image.
        Returns the model's text output.
        """
        ...

    @abstractmethod
    def run_text(self, prompt_text: str, user_text: str) -> str:
        """
        Run text-only inference.
        Returns the model's text output.
        """
        ...
