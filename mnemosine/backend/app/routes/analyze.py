"""
POST /analyze — start a pipeline job.
GET  /jobs/{job_id}/status — job status.
GET  /jobs/{job_id}/results — job results.
"""

from __future__ import annotations

import threading
import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config import get_settings, resolve_device, DeviceType
from ..models_catalog import is_model_allowed
from ..services.job_manager import JobManager
from ..services.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analyze"])


# ── Request / Response models ─────────────────────────

class ModelsSelection(BaseModel):
    vl_metadata: str = ""
    vl_transcription: str = ""
    text_aggregator: str = ""


class AnalyzeRequest(BaseModel):
    manuscript_path: str
    mode: str = Field(default="both", pattern="^(metadata|transcription|both)$")
    granularity: str = Field(default="both", pattern="^(page|work|both)$")
    device: str = Field(default="auto", pattern="^(auto|cpu|cuda|mps)$")
    provider: str = Field(default="openai", pattern="^(hf|openai)$")
    models: ModelsSelection = Field(default_factory=ModelsSelection)


class AnalyzeResponse(BaseModel):
    job_id: str
    output_paths: Dict[str, str] = {}


# ── Endpoints ─────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """
    Start a manuscript analysis pipeline.
    Returns a job_id for progress tracking.
    """
    settings = get_settings()

    # Sanitize: prevent path traversal
    ms_root = Path(settings.manuscripts_root).resolve()
    ms_path = Path(req.manuscript_path).resolve()
    if not str(ms_path).startswith(str(ms_root)):
        # Allow absolute paths that exist (for flexibility), but warn
        if not ms_path.is_dir():
            raise HTTPException(400, f"Manuscript path does not exist: {req.manuscript_path}")

    # Resolve device
    resolved = resolve_device(DeviceType(req.device))

    # Validate models against device (only for HF provider)
    if req.provider == "hf":
        for field_name, model_id in [
            ("vl_metadata", req.models.vl_metadata),
            ("vl_transcription", req.models.vl_transcription),
            ("text_aggregator", req.models.text_aggregator),
        ]:
            if model_id and not is_model_allowed(model_id, resolved):
                raise HTTPException(
                    400,
                    f"Model '{model_id}' requires GPU but device is '{resolved.value}'. "
                    f"Select a CPU-compatible model.",
                )
    elif req.provider == "openai":
        if not settings.openai_api_key or settings.openai_api_key == "your_key_here":
            raise HTTPException(
                400,
                "OPENAI_API_KEY is not set. Please configure it in your .env file before using the OpenAI provider."
            )

    # Create output dir path
    output_dir = ms_path / "OUTPUT"

    # Create job
    job = JobManager.create_job(
        manuscript_path=str(ms_path),
        mode=req.mode,
        granularity=req.granularity,
        output_dir=str(output_dir),
    )

    # Run pipeline in background thread
    def _run():
        try:
            paths = run_pipeline(
                manuscript_path=str(ms_path),
                mode=req.mode,
                granularity=req.granularity,
                device=req.device,
                provider=req.provider,
                models=req.models.model_dump(),
                job_id=job.job_id,
            )
        except Exception as exc:
            logger.error("Pipeline failed for job %s: %s", job.job_id, exc)
            JobManager.mark_failed(job.job_id, str(exc))

    # Try to acquire the global run lock
    if not JobManager.acquire_run_lock():
        raise HTTPException(
            409,
            "Another pipeline is already running. Please wait for it to complete.",
        )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return AnalyzeResponse(job_id=job.job_id)


@router.get("/jobs/{job_id}/status")
async def job_status(job_id: str):
    """Get the current status of a pipeline job."""
    job = JobManager.get_job(job_id)
    if job is None:
        raise HTTPException(404, f"Job not found: {job_id}")
    return job.to_dict()


@router.get("/jobs/{job_id}/results")
async def job_results(job_id: str):
    """Get the results of a completed job."""
    job = JobManager.get_job(job_id)
    if job is None:
        raise HTTPException(404, f"Job not found: {job_id}")
    if job.status.value not in ("completed", "failed"):
        raise HTTPException(
            202, detail={"message": "Job still in progress", "status": job.status.value}
        )
    return job.to_dict()
