# Changelog

All notable changes to Mnemosine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] — 2025-02-24

### Added
- FastAPI backend with full manuscript analysis pipeline
- Per-page metadata extraction via Vision-Language models
- Per-page transcription (OCR) via Vision-Language models
- Work-level metadata aggregation via text-only models
- Dual inference provider support: HuggingFace (local) and OpenAI (API)
- Intelligent model loading/unloading with GPU memory management
- React frontend with Mnemosine UI (violet/lilac theme)
- Metadata and transcription editors with save functionality
- GPU-gated model selection (CPU users limited to small models)
- REST API for integration
- Comprehensive documentation (EN + IT)
- Prompt files for metadata, transcription, and aggregation
