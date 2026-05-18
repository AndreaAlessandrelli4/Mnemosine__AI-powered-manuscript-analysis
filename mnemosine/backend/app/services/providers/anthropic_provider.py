"""
Anthropic Claude inference provider.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .base import InferenceProvider
from ..image_utils import image_to_base64
from ...config import get_settings

logger = logging.getLogger(__name__)


class AnthropicProvider(InferenceProvider):
    """Anthropic Claude API inference for both VL and text tasks."""

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.anthropic_api_key
        self._vision_model = settings.claude_vision_model or "claude-3-5-haiku-latest"
        self._text_model = settings.claude_text_model or "claude-3-5-haiku-latest"
        self._temperature = settings.openai_temperature
        self._max_tokens = settings.openai_max_output_tokens

        if not self._api_key or self._api_key == "your_key_here":
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Configure it in your .env file."
            )

    def _get_client(self):
        from anthropic import Anthropic
        return Anthropic(api_key=self._api_key)

    def run_vl(self, image_path: str | Path, prompt_text: str) -> str:
        client = self._get_client()
        b64_image = image_to_base64(image_path)
        
        # Claude expects specific media type
        ext = Path(image_path).suffix.lower()
        media_type = "image/jpeg"
        if ext == ".png":
            media_type = "image/png"
        elif ext in [".webp"]:
            media_type = "image/webp"

        logger.info(
            "Anthropic VL call: model=%s, image=%s",
            self._vision_model,
            Path(image_path).name,
        )

        try:
            response = client.messages.create(
                model=self._vision_model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": b64_image,
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt_text
                            }
                        ]
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error("Anthropic VL error: %s", e)
            raise ConnectionError(f"Anthropic API failed: {e}")

    def run_text(self, prompt_text: str, user_text: str) -> str:
        client = self._get_client()

        logger.info("Anthropic text call: model=%s", self._text_model)

        try:
            response = client.messages.create(
                model=self._text_model,
                max_tokens=max(self._max_tokens, 2000),
                temperature=self._temperature,
                system=prompt_text,
                messages=[
                    {"role": "user", "content": user_text}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error("Anthropic text error: %s", e)
            raise ConnectionError(f"Anthropic API failed: {e}")
