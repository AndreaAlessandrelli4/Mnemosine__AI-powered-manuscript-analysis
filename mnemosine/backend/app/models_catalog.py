"""
Model catalog — defines available VL and text models with GPU gating.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from .config import detect_device, DeviceType


@dataclass(frozen=True)
class ModelEntry:
    id: str
    type: str            # "vl" or "text"
    label: str           # human-readable description
    requires_gpu: bool   # if True, disabled on CPU


# ── Vision-Language Models ─────────────────────────────

VL_MODELS: List[ModelEntry] = [
    ModelEntry(
        id="Qwen/Qwen3-VL-32B-Instruct",
        type="vl",
        label="Slow, highest performance",
        requires_gpu=True,
    ),
    ModelEntry(
        id="Qwen/Qwen3-VL-8B-Instruct",
        type="vl",
        label="Medium, good performance (GPU default)",
        requires_gpu=True,
    ),
    ModelEntry(
        id="Qwen/Qwen3-VL-4B-Instruct",
        type="vl",
        label="Fast, medium performance",
        requires_gpu=True,
    ),
    ModelEntry(
        id="Qwen/Qwen3-VL-2B-Instruct",
        type="vl",
        label="Very fast, low performance (CPU default)",
        requires_gpu=False,
    ),
]

# ── Text-Only Models ──────────────────────────────────

TEXT_MODELS: List[ModelEntry] = [
    ModelEntry(
        id="Qwen/Qwen2.5-32B-Instruct",
        type="text",
        label="Slow, highest performance",
        requires_gpu=True,
    ),
    ModelEntry(
        id="Qwen/Qwen2.5-14B-Instruct",
        type="text",
        label="Medium, good performance",
        requires_gpu=True,
    ),
    ModelEntry(
        id="Qwen/Qwen2.5-7B-Instruct",
        type="text",
        label="Fast, good performance (GPU default)",
        requires_gpu=True,
    ),
    ModelEntry(
        id="Qwen/Qwen2.5-3B-Instruct",
        type="text",
        label="Very fast, lower performance (CPU default)",
        requires_gpu=False,
    ),
]

ALL_MODELS = VL_MODELS + TEXT_MODELS

# ── Lookup Helpers ────────────────────────────────────

_MODEL_MAP: Dict[str, ModelEntry] = {m.id: m for m in ALL_MODELS}


def get_model(model_id: str) -> ModelEntry | None:
    return _MODEL_MAP.get(model_id)


def is_model_allowed(model_id: str, device: DeviceType) -> bool:
    """Check if a model is allowed on the given device."""
    entry = get_model(model_id)
    if entry is None:
        return False
    if entry.requires_gpu and device == DeviceType.CPU:
        return False
    return True


def default_vl_model(device: DeviceType) -> str:
    """Return the default VL model ID based on device."""
    if device in (DeviceType.CUDA, DeviceType.MPS):
        return "Qwen/Qwen3-VL-8B-Instruct"
    return "Qwen/Qwen3-VL-2B-Instruct"


def default_text_model(device: DeviceType) -> str:
    """Return the default text model ID based on device."""
    if device in (DeviceType.CUDA, DeviceType.MPS):
        return "Qwen/Qwen2.5-7B-Instruct"
    return "Qwen/Qwen2.5-3B-Instruct"


def get_catalog() -> Dict[str, Any]:
    """Return full model catalog with GPU availability info."""
    detected = detect_device()
    gpu_available = detected in (DeviceType.CUDA, DeviceType.MPS)

    return {
        "models": [asdict(m) for m in ALL_MODELS],
        "gpu_available": gpu_available,
        "detected_device": detected.value,
        "recommended_device": "auto",
        "defaults": {
            "vl": default_vl_model(detected),
            "text": default_text_model(detected),
        },
    }
