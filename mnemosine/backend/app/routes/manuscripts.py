"""
Manuscript browsing and content CRUD endpoints.

- GET  /manuscripts/browse      — list manuscripts
- GET  /pages                   — list pages of a manuscript
- GET  /pages/{page}/metadata   — get page metadata
- PUT  /pages/{page}/metadata   — update page metadata
- GET  /pages/{page}/transcription  — get page transcription
- PUT  /pages/{page}/transcription  — update page transcription
- GET  /work/metadata           — get work-level metadata
- POST /work/metadata/regenerate — regenerate aggregated metadata
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..config import get_settings
from ..services.image_utils import list_images, parse_page_number, SUPPORTED_EXTENSIONS
from ..services.json_repair import ensure_json_string
from ..services.prompt_loader import get_aggregation_prompt
from ..services.pipeline import create_provider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["manuscripts"])


# ── Models ────────────────────────────────────────────

class PageInfo(BaseModel):
    page_number: int
    filename: str
    has_metadata: bool = False
    has_transcription: bool = False


class MetadataBody(BaseModel):
    content: str


class TranscriptionBody(BaseModel):
    content: str


# ── Browse ────────────────────────────────────────────

@router.get("/manuscripts/browse")
async def browse_manuscripts(path: Optional[str] = Query(None)):
    """
    List subdirectories in the manuscripts root (or a given path).
    Returns directories that have an Immagini/ subfolder.
    """
    settings = get_settings()
    root = Path(path) if path else Path(settings.manuscripts_root)
    root = root.resolve()

    if not root.is_dir():
        raise HTTPException(404, f"Directory not found: {root}")

    results = []
    for entry in sorted(os.listdir(root)):
        full = root / entry
        if full.is_dir():
            has_images = (full / "Immagini").is_dir()
            has_output = (full / "OUTPUT").is_dir()
            results.append({
                "name": entry,
                "path": str(full),
                "has_images": has_images,
                "has_output": has_output,
            })

    return {"manuscripts": results, "current_path": str(root)}


# ── Pages ─────────────────────────────────────────────

@router.get("/pages", response_model=List[PageInfo])
async def get_pages(manuscript_path: str = Query(...)):
    """List all pages in a manuscript with availability flags."""
    ms_path = Path(manuscript_path).resolve()
    images_dir = ms_path / "Immagini"
    if not images_dir.is_dir():
        raise HTTPException(404, f"Immagini directory not found in {ms_path}")

    meta_dir = ms_path / "OUTPUT" / "page_metadati"
    trasc_dir = ms_path / "OUTPUT" / "Trascrizioni"

    images = list_images(images_dir)
    pages = []
    for page_num, filename in images:
        stem = Path(filename).stem
        pages.append(PageInfo(
            page_number=page_num,
            filename=filename,
            has_metadata=(meta_dir / f"{stem}.txt").exists() if meta_dir.exists() else False,
            has_transcription=(trasc_dir / f"{stem}.txt").exists() if trasc_dir.exists() else False,
        ))
    return pages


# ── Page Metadata CRUD ────────────────────────────────

@router.get("/pages/{page_filename}/metadata")
async def get_page_metadata(page_filename: str, manuscript_path: str = Query(...)):
    """Get metadata JSON for a specific page."""
    stem = Path(page_filename).stem
    meta_path = Path(manuscript_path).resolve() / "OUTPUT" / "page_metadati" / f"{stem}.txt"
    if not meta_path.exists():
        raise HTTPException(404, f"Metadata not found: {stem}")
    content = meta_path.read_text(encoding="utf-8")
    return {"filename": page_filename, "content": content}


@router.put("/pages/{page_filename}/metadata")
async def update_page_metadata(
    page_filename: str,
    body: MetadataBody,
    manuscript_path: str = Query(...),
):
    """Update metadata for a specific page. Marks work metadata as stale."""
    stem = Path(page_filename).stem
    ms_path = Path(manuscript_path).resolve()
    meta_dir = ms_path / "OUTPUT" / "page_metadati"
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_path = meta_dir / f"{stem}.txt"

    # Validate JSON
    try:
        json_str = ensure_json_string(body.content)
    except ValueError:
        json_str = body.content  # save as-is if not JSON

    meta_path.write_text(json_str, encoding="utf-8")

    # Mark work metadata as stale
    stale_path = ms_path / "OUTPUT" / ".metadata_opera_stale"
    stale_path.touch()

    return {"saved": True, "filename": page_filename, "stale": True}


# ── Page Transcription CRUD ──────────────────────────

@router.get("/pages/{page_filename}/transcription")
async def get_page_transcription(page_filename: str, manuscript_path: str = Query(...)):
    """Get transcription text for a specific page."""
    stem = Path(page_filename).stem
    trasc_path = Path(manuscript_path).resolve() / "OUTPUT" / "Trascrizioni" / f"{stem}.txt"
    if not trasc_path.exists():
        raise HTTPException(404, f"Transcription not found: {stem}")
    content = trasc_path.read_text(encoding="utf-8")
    return {"filename": page_filename, "content": content}


@router.put("/pages/{page_filename}/transcription")
async def update_page_transcription(
    page_filename: str,
    body: TranscriptionBody,
    manuscript_path: str = Query(...),
):
    """Update transcription for a specific page."""
    stem = Path(page_filename).stem
    trasc_dir = Path(manuscript_path).resolve() / "OUTPUT" / "Trascrizioni"
    trasc_dir.mkdir(parents=True, exist_ok=True)
    trasc_path = trasc_dir / f"{stem}.txt"
    trasc_path.write_text(body.content, encoding="utf-8")
    return {"saved": True, "filename": page_filename}


# ── Work Metadata ────────────────────────────────────

@router.get("/work/metadata")
async def get_work_metadata(manuscript_path: str = Query(...)):
    """Get work-level aggregated metadata."""
    ms_path = Path(manuscript_path).resolve()
    opera_path = ms_path / "OUTPUT" / "metadata_opera.txt"
    stale_path = ms_path / "OUTPUT" / ".metadata_opera_stale"

    if not opera_path.exists():
        raise HTTPException(404, "Work metadata not generated yet")

    content = opera_path.read_text(encoding="utf-8")
    is_stale = stale_path.exists()

    return {
        "content": content,
        "is_stale": is_stale,
        "path": str(opera_path),
    }


@router.put("/work/metadata")
async def update_work_metadata(
    body: MetadataBody,
    manuscript_path: str = Query(...),
):
    """Update work-level aggregated metadata."""
    ms_path = Path(manuscript_path).resolve()
    opera_dir = ms_path / "OUTPUT"
    opera_dir.mkdir(parents=True, exist_ok=True)
    opera_path = opera_dir / "metadata_opera.txt"
    stale_path = opera_dir / ".metadata_opera_stale"

    # Validate JSON
    try:
        json_str = ensure_json_string(body.content)
    except ValueError:
        json_str = body.content

    opera_path.write_text(json_str, encoding="utf-8")

    # Clear stale flag since it's intentionally updated
    if stale_path.exists():
        stale_path.unlink()

    return {"saved": True, "path": str(opera_path)}


@router.post("/work/metadata/regenerate")
async def regenerate_work_metadata(
    manuscript_path: str = Query(...),
    provider: str = Query(default="openai"),
    device: str = Query(default="auto"),
    text_model: str = Query(default=""),
):
    """
    Regenerate work-level metadata from per-page metadata files.
    Uses prompt_aggregation_metadati.txt.
    """
    ms_path = Path(manuscript_path).resolve()
    meta_dir = ms_path / "OUTPUT" / "page_metadati"

    if not meta_dir.is_dir():
        raise HTTPException(404, "No per-page metadata found. Run analysis first.")

    settings = get_settings()

    # Collect per-page metadata
    all_meta = []
    for idx, f in enumerate(sorted(meta_dir.glob("*.txt")), 1):
        content = f.read_text(encoding="utf-8")
        all_meta.append(f"\n\nINPUT {idx}:\n{content}")

    if not all_meta:
        raise HTTPException(404, "No per-page metadata files found.")

    joined = "".join(all_meta)

    # Get aggregation prompt
    prompt_dir = Path(settings.prompt_dir)
    aggregation_prompt = get_aggregation_prompt(prompt_dir)

    # Run text inference
    inf_provider = create_provider(provider, device)
    try:
        if provider == "hf" and text_model:
            raw = inf_provider.run_text(aggregation_prompt, joined, model_id=text_model)
        else:
            raw = inf_provider.run_text(aggregation_prompt, joined)

        # Repair JSON
        try:
            result = ensure_json_string(raw)
        except ValueError:
            result = raw

        # Save
        opera_path = ms_path / "OUTPUT" / "metadata_opera.txt"
        opera_path.write_text(result, encoding="utf-8")

        # Remove stale marker
        stale_path = ms_path / "OUTPUT" / ".metadata_opera_stale"
        if stale_path.exists():
            stale_path.unlink()

        return {"regenerated": True, "content": result}

    except Exception as exc:
        logger.error("Regeneration failed: %s", exc)
        raise HTTPException(500, f"Regeneration failed: {exc}")
    finally:
        # Cleanup HF model if used
        if provider == "hf" and hasattr(inf_provider, "unload"):
            inf_provider.unload()


# ── Image serving ────────────────────────────────────

@router.get("/pages/{page_filename}/image")
async def get_page_image(page_filename: str, manuscript_path: str = Query(...)):
    """Serve a page image."""
    from fastapi.responses import FileResponse

    ms_path = Path(manuscript_path).resolve()
    image_path = ms_path / "Immagini" / page_filename

    if not image_path.exists():
        raise HTTPException(404, f"Image not found: {page_filename}")

    return FileResponse(str(image_path))
