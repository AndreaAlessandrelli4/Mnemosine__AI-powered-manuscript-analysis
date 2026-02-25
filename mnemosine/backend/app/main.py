"""
Mnemosine — FastAPI Application Entry Point.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import health, models, analyze, manuscripts

# ── Logging ───────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Mnemosine starting up...")
    yield
    # Cleanup: unload any loaded model
    try:
        from .model_manager import ModelManager
        ModelManager().unload()
        logger.info("Model unloaded on shutdown.")
    except Exception:
        pass
    logger.info("Mnemosine shut down.")


# ── App ───────────────────────────────────────────────

app = FastAPI(
    title="Mnemosine",
    description="Manuscript analysis tool for the Ministry of Culture (MiC). "
                "Extracts metadata and transcriptions from manuscript scans using "
                "Vision-Language and text-only models.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────

app.include_router(health.router)
app.include_router(models.router)
app.include_router(analyze.router)
app.include_router(manuscripts.router)
