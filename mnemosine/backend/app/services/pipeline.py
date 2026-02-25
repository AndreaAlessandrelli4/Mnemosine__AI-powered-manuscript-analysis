"""
Pipeline — orchestrates the full manuscript analysis workflow.

Steps:
1. Validate manuscript structure (Immagini/ exists, create OUTPUT/ if needed)
2. Enumerate images, sort by page number
3. If mode includes metadata: VL inference per page → JSON repair → save
4. If mode includes transcription: VL inference per page → save text
5. If granularity includes work AND mode includes metadata:
   - Unload VL model (free memory)
   - Load text-only aggregator
   - Read per-page JSONs, generate work-level metadata → save
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Dict, Optional

from .image_utils import list_images
from .json_repair import ensure_json_string
from .prompt_loader import (
    get_aggregation_prompt,
    get_metadata_prompt,
    get_transcription_prompt,
)
from .job_manager import JobManager
from .providers.base import InferenceProvider
from ..config import get_settings, InferenceProvider as ProviderEnum, resolve_device, DeviceType
from ..models_catalog import is_model_allowed

logger = logging.getLogger(__name__)

# Global lock: one pipeline at a time
_pipeline_lock = threading.Lock()


def create_provider(
    provider: str,
    device: str = "auto",
) -> InferenceProvider:
    """Factory: create the appropriate inference provider."""
    if provider == "openai":
        from .providers.openai_provider import OpenAIProvider
        return OpenAIProvider()
    else:
        from .providers.hf_provider import HFProvider
        return HFProvider(device=device)


def validate_manuscript(manuscript_path: str) -> Path:
    """
    Validate that the manuscript directory has the expected structure.
    Creates OUTPUT/ if it doesn't exist.
    Returns the manuscript path as Path.
    """
    ms_path = Path(manuscript_path).resolve()
    if not ms_path.is_dir():
        raise ValueError(f"Manuscript directory does not exist: {ms_path}")

    images_dir = ms_path / "Immagini"
    if not images_dir.is_dir():
        raise ValueError(f"Immagini directory not found: {images_dir}")

    output_dir = ms_path / "OUTPUT"
    output_dir.mkdir(exist_ok=True)

    return ms_path


def run_pipeline(
    manuscript_path: str,
    mode: str = "both",            # "metadata" | "transcription" | "both"
    granularity: str = "both",     # "page" | "work" | "both"
    device: str = "auto",
    provider: str = "openai",
    models: Optional[Dict[str, str]] = None,
    job_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Run the full analysis pipeline.
    Returns dict of output paths.
    """
    if not _pipeline_lock.acquire(blocking=False):
        raise RuntimeError("A pipeline is already running. Please wait.")

    try:
        return _run_pipeline_internal(
            manuscript_path, mode, granularity, device, provider, models, job_id
        )
    finally:
        _pipeline_lock.release()


def _run_pipeline_internal(
    manuscript_path: str,
    mode: str,
    granularity: str,
    device: str,
    provider: str,
    models: Optional[Dict[str, str]],
    job_id: Optional[str],
) -> Dict[str, str]:
    settings = get_settings()
    prompt_dir = Path(settings.prompt_dir)
    resolved_device = resolve_device(DeviceType(device))
    models = models or {}

    # Validate model selection against device
    for key, model_id in models.items():
        if model_id and not is_model_allowed(model_id, resolved_device):
            # For OpenAI provider, model IDs from HF catalog aren't used
            if provider != "openai":
                raise ValueError(
                    f"Model '{model_id}' requires GPU but device is {resolved_device.value}. "
                    f"Select a smaller model or use a GPU."
                )

    if job_id:
        JobManager.mark_running(job_id)

    # Step 1: Validate manuscript structure
    ms_path = validate_manuscript(manuscript_path)
    output_dir = ms_path / "OUTPUT"
    images_dir = ms_path / "Immagini"

    # Step 2: Enumerate images
    images = list_images(images_dir)
    if not images:
        raise ValueError(f"No supported images found in {images_dir}")

    total_pages = len(images)
    output_paths: Dict[str, str] = {}

    do_metadata = mode in ("metadata", "both")
    do_transcription = mode in ("transcription", "both")
    do_work = granularity in ("work", "both") and do_metadata

    logger.info(
        "Pipeline: %d pages, mode=%s, granularity=%s, device=%s, provider=%s",
        total_pages, mode, granularity, resolved_device.value, provider,
    )

    # Create provider
    inf_provider = create_provider(provider, device)
    is_hf = provider == "hf"

    # Step 3: Per-page metadata extraction
    if do_metadata:
        meta_dir = output_dir / "page_metadati"
        meta_dir.mkdir(exist_ok=True)
        output_paths["page_metadati"] = str(meta_dir)

        metadata_prompt = get_metadata_prompt(prompt_dir)
        vl_model = models.get("vl_metadata", "")

        for i, (page_num, filename) in enumerate(images):
            if job_id:
                JobManager.update_progress(
                    job_id, i, total_pages * (2 if do_transcription else 1),
                    f"Extracting metadata: page {page_num} ({filename})",
                )

            image_path = images_dir / filename
            try:
                if is_hf:
                    raw = inf_provider.run_vl(image_path, metadata_prompt, model_id=vl_model)
                else:
                    raw = inf_provider.run_vl(image_path, metadata_prompt)

                # JSON repair
                try:
                    json_str = ensure_json_string(raw)
                except ValueError as e:
                    logger.warning("JSON repair failed for %s: %s", filename, e)
                    json_str = raw  # save raw anyway
                    if job_id:
                        JobManager.add_error(job_id, f"JSON repair failed: {filename}")

                # Save
                out_name = Path(filename).stem + ".txt"
                out_path = meta_dir / out_name
                out_path.write_text(json_str, encoding="utf-8")
                logger.info("Saved metadata: %s", out_path.name)

            except Exception as exc:
                logger.error("Metadata extraction failed for %s: %s", filename, exc)
                if job_id:
                    JobManager.add_error(job_id, f"Metadata error: {filename}: {exc}")

    # Step 4: Per-page transcription
    if do_transcription:
        trasc_dir = output_dir / "Trascrizioni"
        trasc_dir.mkdir(exist_ok=True)
        output_paths["trascrizioni"] = str(trasc_dir)

        transcription_prompt = get_transcription_prompt(prompt_dir)
        vl_model = models.get("vl_transcription", "")
        offset = total_pages if do_metadata else 0

        for i, (page_num, filename) in enumerate(images):
            if job_id:
                JobManager.update_progress(
                    job_id, offset + i, total_pages * (2 if do_metadata else 1),
                    f"Transcribing: page {page_num} ({filename})",
                )

            image_path = images_dir / filename
            try:
                if is_hf:
                    raw = inf_provider.run_vl(image_path, transcription_prompt, model_id=vl_model)
                else:
                    raw = inf_provider.run_vl(image_path, transcription_prompt)

                # Save plain text
                out_name = Path(filename).stem + ".txt"
                out_path = trasc_dir / out_name
                out_path.write_text(raw.strip(), encoding="utf-8")
                logger.info("Saved transcription: %s", out_path.name)

            except Exception as exc:
                logger.error("Transcription failed for %s: %s", filename, exc)
                if job_id:
                    JobManager.add_error(job_id, f"Transcription error: {filename}: {exc}")

    # Step 5: Work-level aggregation
    if do_work:
        if job_id:
            JobManager.update_progress(
                job_id, 0, 1,
                "Aggregating work-level metadata",
            )

        # Unload VL model if using HF to free memory
        if is_hf and hasattr(inf_provider, "unload"):
            logger.info("Unloading VL model before aggregation")
            inf_provider.unload()

        try:
            aggregation_prompt = get_aggregation_prompt(prompt_dir)

            # Collect per-page metadata
            meta_dir = output_dir / "page_metadati"
            all_meta_texts = []
            sorted_files = sorted(meta_dir.glob("*.txt"))
            for idx, f in enumerate(sorted_files, 1):
                content = f.read_text(encoding="utf-8")
                all_meta_texts.append(f"\n\nINPUT {idx}:\n{content}")

            joined = "".join(all_meta_texts)

            # Run text aggregation
            text_model = models.get("text_aggregator", "")
            if is_hf:
                raw_agg = inf_provider.run_text(
                    aggregation_prompt, joined, model_id=text_model
                )
            else:
                raw_agg = inf_provider.run_text(aggregation_prompt, joined)

            # JSON repair on aggregation result
            try:
                agg_json = ensure_json_string(raw_agg)
            except ValueError:
                agg_json = raw_agg
                if job_id:
                    JobManager.add_error(job_id, "JSON repair failed for metadata_opera")

            # Save
            opera_path = output_dir / "metadata_opera.txt"
            opera_path.write_text(agg_json, encoding="utf-8")
            output_paths["metadata_opera"] = str(opera_path)
            logger.info("Saved work metadata: %s", opera_path)

        except Exception as exc:
            logger.error("Aggregation failed: %s", exc)
            if job_id:
                JobManager.add_error(job_id, f"Aggregation error: {exc}")

    # Final cleanup for HF
    if is_hf and hasattr(inf_provider, "unload"):
        inf_provider.unload()

    # Mark job completed
    if job_id:
        job = JobManager.get_job(job_id)
        total = total_pages * ((1 if do_metadata else 0) + (1 if do_transcription else 0))
        JobManager.update_progress(job_id, total, total, "Completed")
        if job and not job.errors:
            JobManager.mark_completed(job_id, output_paths)
        else:
            JobManager.mark_completed(job_id, output_paths)

    return output_paths
