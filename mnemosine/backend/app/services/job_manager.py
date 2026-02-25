"""
Job Manager — tracks pipeline jobs, persists status to OUTPUT/status.json.

One job at a time (global lock).
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInfo:
    """In-memory representation of a job."""

    def __init__(
        self,
        job_id: str,
        manuscript_path: str,
        mode: str,
        granularity: str,
        output_dir: str,
    ):
        self.job_id = job_id
        self.manuscript_path = manuscript_path
        self.mode = mode
        self.granularity = granularity
        self.output_dir = output_dir
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.total_pages = 0
        self.processed_pages = 0
        self.current_step = ""
        self.errors: List[str] = []
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.output_paths: Dict[str, str] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "manuscript_path": self.manuscript_path,
            "mode": self.mode,
            "granularity": self.granularity,
            "status": self.status.value,
            "progress": round(self.progress, 2),
            "total_pages": self.total_pages,
            "processed_pages": self.processed_pages,
            "current_step": self.current_step,
            "errors": self.errors,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "output_paths": self.output_paths,
        }


class JobManager:
    """Manages pipeline job lifecycles."""

    _lock = threading.Lock()
    _jobs: Dict[str, JobInfo] = {}
    _running_lock = threading.Lock()  # global lock: 1 job at a time

    @classmethod
    def create_job(
        cls,
        manuscript_path: str,
        mode: str,
        granularity: str,
        output_dir: str,
    ) -> JobInfo:
        job_id = str(uuid.uuid4())[:8]
        job = JobInfo(job_id, manuscript_path, mode, granularity, output_dir)
        with cls._lock:
            cls._jobs[job_id] = job
        return job

    @classmethod
    def get_job(cls, job_id: str) -> Optional[JobInfo]:
        return cls._jobs.get(job_id)

    @classmethod
    def update_progress(
        cls,
        job_id: str,
        processed: int,
        total: int,
        step: str = "",
    ) -> None:
        job = cls.get_job(job_id)
        if job is None:
            return
        job.processed_pages = processed
        job.total_pages = total
        job.progress = (processed / total * 100) if total > 0 else 0
        job.current_step = step
        cls._persist_status(job)

    @classmethod
    def mark_running(cls, job_id: str) -> None:
        job = cls.get_job(job_id)
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc).isoformat()
            cls._persist_status(job)

    @classmethod
    def mark_completed(cls, job_id: str, output_paths: Dict[str, str]) -> None:
        job = cls.get_job(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.output_paths = output_paths
            cls._persist_status(job)

    @classmethod
    def mark_failed(cls, job_id: str, error: str) -> None:
        job = cls.get_job(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.errors.append(error)
            job.completed_at = datetime.now(timezone.utc).isoformat()
            cls._persist_status(job)

    @classmethod
    def add_error(cls, job_id: str, error: str) -> None:
        job = cls.get_job(job_id)
        if job:
            job.errors.append(error)

    @classmethod
    def acquire_run_lock(cls) -> bool:
        """Try to acquire the global run lock (non-blocking)."""
        return cls._running_lock.acquire(blocking=False)

    @classmethod
    def release_run_lock(cls) -> None:
        try:
            cls._running_lock.release()
        except RuntimeError:
            pass

    @classmethod
    def _persist_status(cls, job: JobInfo) -> None:
        """Write status.json to the OUTPUT directory."""
        try:
            output_dir = Path(job.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            status_path = output_dir / "status.json"
            with open(status_path, "w", encoding="utf-8") as f:
                json.dump(job.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning("Failed to persist status for job %s: %s", job.job_id, exc)
