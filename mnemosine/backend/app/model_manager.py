"""
ModelManager — singleton that handles model loading/unloading with memory cleanup.

Key responsibilities:
- Keep track of the currently loaded model
- Unload before loading a new model
- Clean GPU/MPS memory after unloading
- Global lock to prevent concurrent loading
"""

from __future__ import annotations

import gc
import logging
import threading
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Manages exactly ONE model at a time (VL or text).
    Thread-safe via a global lock.  Supports CUDA and MPS cleanup.
    """

    _instance: Optional["ModelManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ModelManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._model = None
                    cls._instance._processor = None
                    cls._instance._model_id = None
                    cls._instance._device = None
                    cls._instance._model_type = None  # "vl" or "text"
        return cls._instance

    # ── Public API ────────────────────────────────────

    @property
    def current_model_id(self) -> Optional[str]:
        return self._model_id

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(
        self,
        model_id: str,
        device: str = "cpu",
        model_type: str = "vl",
    ) -> Tuple[Any, Any]:
        """
        Load a model.  If a different model is already loaded, unload it first.
        Returns (model_or_pipeline, processor_or_None).
        """
        with self._lock:
            if self._model_id == model_id and self._model is not None:
                logger.info("Model %s already loaded — reusing.", model_id)
                return self._model, self._processor

            # Unload previous if different
            if self._model is not None:
                logger.info("Unloading previous model %s before loading %s", self._model_id, model_id)
                self._unload_internal()

            logger.info("Loading model %s on device=%s (type=%s)", model_id, device, model_type)
            model, processor = self._load_model(model_id, device, model_type)
            self._model = model
            self._processor = processor
            self._model_id = model_id
            self._device = device
            self._model_type = model_type
            return model, processor

    def unload(self) -> None:
        """Unload the current model and free memory."""
        with self._lock:
            self._unload_internal()

    def get_current(self) -> Tuple[Optional[Any], Optional[Any]]:
        """Return currently loaded (model, processor) or (None, None)."""
        return self._model, self._processor

    # ── Internal ──────────────────────────────────────

    def _unload_internal(self) -> None:
        if self._model is None:
            return
        logger.info("Unloading model %s", self._model_id)
        del self._model
        del self._processor
        self._model = None
        self._processor = None
        self._model_id = None
        self._model_type = None
        gc.collect()
        self._clear_gpu_cache()

    @staticmethod
    def _clear_gpu_cache() -> None:
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("Cleared CUDA cache")
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                if hasattr(torch.mps, "empty_cache"):
                    torch.mps.empty_cache()
                    logger.debug("Cleared MPS cache")
        except ImportError:
            pass

    @staticmethod
    def _load_model(
        model_id: str,
        device: str,
        model_type: str,
    ) -> Tuple[Any, Any]:
        """
        Load a HuggingFace model.  Returns (pipeline, None).
        Uses transformers pipeline API for simplicity.
        """
        try:
            from transformers import pipeline as hf_pipeline
            import torch
        except ImportError as exc:
            raise RuntimeError(
                "HuggingFace provider requires 'transformers' and 'torch'. "
                "Install them: pip install torch transformers accelerate"
            ) from exc

        # Determine torch device
        if device == "cuda" and torch.cuda.is_available():
            torch_device = "cuda"
        elif device == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch_device = "mps"
        else:
            torch_device = "cpu"

        if model_type == "vl":
            pipe = hf_pipeline(
                "image-text-to-text",
                model=model_id,
                device=torch_device,
            )
        else:
            pipe = hf_pipeline(
                "text-generation",
                model=model_id,
                device=torch_device,
            )

        return pipe, None
