"""
OpenAI inference provider — uses official OpenAI SDK for demo/testing.

Model names are configurable via environment variables (OPENAI_VISION_MODEL,
OPENAI_TEXT_MODEL).  Never hardcoded.

Cost control:
- Low temperature (0.2)
- Reasonable max_output_tokens (1200)
- No double calls unless JSON repair fails
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .base import InferenceProvider
from ..image_utils import image_to_base64
from ...config import get_settings

logger = logging.getLogger(__name__)


class OpenAIProvider(InferenceProvider):
    """OpenAI API inference for both VL (vision) and text tasks."""

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.openai_api_key
        self._base_url = settings.openai_base_url
        self._vision_model = settings.openai_vision_model or "gpt-4o-mini"
        self._text_model = settings.openai_text_model or "gpt-4o-mini"
        self._temperature = settings.openai_temperature
        self._max_tokens = settings.openai_max_output_tokens

        if not self._api_key or self._api_key == "your_key_here":
            raise ValueError(
                "OPENAI_API_KEY is not set. Configure it in your .env file."
            )

    def _get_client(self):
        """Create OpenAI client lazily."""
        from openai import OpenAI

        kwargs = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return OpenAI(**kwargs)

    def run_vl(self, image_path: str | Path, prompt_text: str) -> str:
        """
        Vision-language inference via OpenAI.
        Sends image as base64 inline with the prompt.
        """
        client = self._get_client()
        b64_image = image_to_base64(image_path)

        logger.info(
            "OpenAI VL call: model=%s, image=%s",
            self._vision_model,
            Path(image_path).name,
        )

        try:
            response = client.chat.completions.create(
                model=self._vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_text,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_image}"
                                },
                            },
                        ],
                    }
                ],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("OpenAI VL error: %s", e)
            raise ConnectionError(f"OpenAI API failed: {e}")

    def run_text(self, prompt_text: str, user_text: str) -> str:
        """
        Text-only inference via OpenAI.
        System prompt = prompt file content; user message = aggregated page data.
        """
        client = self._get_client()

        logger.info("OpenAI text call: model=%s", self._text_model)

        try:
            response = client.chat.completions.create(
                model=self._text_model,
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": user_text},
                ],
                temperature=self._temperature,
                max_tokens=max(self._max_tokens, 2000),  # aggregation may need more
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("OpenAI text error: %s", e)
            raise ConnectionError(f"OpenAI API failed: {e}")
