"""
Google Generative AI inference provider.

Model names are configurable via environment variables (GOOGLE_VISION_MODEL,
GOOGLE_TEXT_MODEL).
"""

from __future__ import annotations

import logging
from pathlib import Path

from .base import InferenceProvider
from ...config import get_settings
from PIL import Image

logger = logging.getLogger(__name__)


class GoogleProvider(InferenceProvider):
    """Google Gemini API inference for both VL and text tasks."""

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.google_api_key
        self._vision_model = settings.google_vision_model or "gemini-2.5-flash"
        self._text_model = settings.google_text_model or "gemini-2.5-flash"
        self._temperature = settings.openai_temperature
        self._max_tokens = settings.openai_max_output_tokens

        if not self._api_key or self._api_key == "your_key_here":
            raise ValueError(
                "GOOGLE_API_KEY is not set. Configure it in your .env file."
            )

        import google.generativeai as genai
        genai.configure(api_key=self._api_key)
        self.genai = genai

    def run_vl(self, image_path: str | Path, prompt_text: str) -> str:
        logger.info(
            "Google VL call: model=%s, image=%s",
            self._vision_model,
            Path(image_path).name,
        )

        try:
            model = self.genai.GenerativeModel(self._vision_model)
            img = Image.open(image_path)
            response = model.generate_content(
                [prompt_text, img],
                generation_config=self.genai.types.GenerationConfig(
                    temperature=self._temperature,
                    max_output_tokens=self._max_tokens,
                )
            )
            return response.text
        except Exception as e:
            logger.error("Google VL error: %s", e)
            raise ConnectionError(f"Google API failed: {e}")

    def run_text(self, prompt_text: str, user_text: str) -> str:
        logger.info("Google text call: model=%s", self._text_model)

        try:
            model = self.genai.GenerativeModel(
                self._text_model,
                system_instruction=prompt_text
            )
            response = model.generate_content(
                user_text,
                generation_config=self.genai.types.GenerationConfig(
                    temperature=self._temperature,
                    max_output_tokens=max(self._max_tokens, 2000),
                )
            )
            return response.text
        except Exception as e:
            logger.error("Google text error: %s", e)
            raise ConnectionError(f"Google API failed: {e}")
