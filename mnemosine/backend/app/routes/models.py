"""
GET /models/catalog — returns the model catalog with GPU info.
"""

from fastapi import APIRouter

from ..models_catalog import get_catalog

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/catalog")
async def models_catalog():
    """
    Return the full catalog of available models.
    Includes GPU availability, detected device, defaults,
    and per-model requires_gpu flag for frontend gating.
    """
    return get_catalog()
