"""
Qwen inference provider (OpenAI compatible via DashScope).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .base import InferenceProvider
from ..image_utils import image_to_base64
from ...config import get_settings

logger = logging.getLogger(__name__)


class QwenProvider(InferenceProvider):
    """Qwen API inference using OpenAI SDK via Alibaba DashScope."""

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.qwen_api_key
        self._base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self._vision_model = settings.qwen_vision_model or "qwen-vl-plus"
        self._text_model = settings.qwen_text_model or "qwen-plus"
        self._temperature = settings.openai_temperature
        self._max_tokens = settings.openai_max_output_tokens

        if not self._api_key or self._api_key == "your_key_here":
            raise ValueError(
                "QWEN_API_KEY is not set. Configure it in your .env file."
            )

    def _get_client(self):
        """Create OpenAI client lazily."""
        from openai import OpenAI
        return OpenAI(api_key=self._api_key, base_url=self._base_url)

    def run_vl(self, image_path: str | Path, prompt_text: str) -> str:
        """
        Vision-language inference via Qwen.
        """
        client = self._get_client()
        b64_image = image_to_base64(image_path)

        logger.info(
            "Qwen VL call: model=%s, image=%s",
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
            logger.error("Qwen VL error: %s", e)
            raise ConnectionError(f"Qwen API failed: {e}")

    def run_text(self, prompt_text: str, user_text: str) -> str:
        """
        Text-only inference via Qwen.
        """
        client = self._get_client()

        logger.info("Qwen text call: model=%s", self._text_model)

        try:
            response = client.chat.completions.create(
                model=self._text_model,
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": user_text},
                ],
                temperature=self._temperature,
                max_tokens=max(self._max_tokens, 2000),
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Qwen text error: %s", e)
            raise ConnectionError(f"Qwen API failed: {e}")
