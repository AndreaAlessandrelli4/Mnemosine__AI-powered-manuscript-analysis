"""
HuggingFace inference provider — runs Qwen VL and text models locally
via the transformers pipeline API.

Integrates with ModelManager for proper load/unload lifecycle.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

from .base import InferenceProvider
from ...model_manager import ModelManager
from ...config import resolve_device, DeviceType

logger = logging.getLogger(__name__)


class HFProvider(InferenceProvider):
    """Local HuggingFace inference using transformers pipelines."""

    def __init__(self, device: str = "auto"):
        self.device = resolve_device(DeviceType(device))
        self.manager = ModelManager()

    def run_vl(self, image_path: str | Path, prompt_text: str, model_id: str = "") -> str:
        """Vision-language inference with a loaded VL pipeline."""
        if not model_id:
            from ...models_catalog import default_vl_model
            model_id = default_vl_model(self.device)

        pipe, _ = self.manager.load(model_id, self.device.value, model_type="vl")

        # Open image
        img = Image.open(image_path).convert("RGB")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": prompt_text},
                ],
            },
        ]

        result = pipe(
            text=messages,
            max_new_tokens=5000,
            do_sample=False,
            return_full_text=False,
        )
        return result[0]["generated_text"]

    def run_text(self, prompt_text: str, user_text: str, model_id: str = "") -> str:
        """Text-only inference with a loaded text pipeline."""
        if not model_id:
            from ...models_catalog import default_text_model
            model_id = default_text_model(self.device)

        pipe, _ = self.manager.load(model_id, self.device.value, model_type="text")

        messages = [
            {"role": "system", "content": prompt_text},
            {"role": "user", "content": user_text},
        ]

        result = pipe(
            text=messages,
            max_new_tokens=5000,
            do_sample=False,
            return_full_text=False,
        )
        return result[0]["generated_text"]

    def unload(self) -> None:
        """Explicitly unload the model (e.g., between VL and text phases)."""
        self.manager.unload()
