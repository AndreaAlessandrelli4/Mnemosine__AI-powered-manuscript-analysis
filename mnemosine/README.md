# Mnemosine

**AI-powered manuscript analysis for the Italian Ministry of Culture (MiC).**

Mnemosine extracts structured metadata and transcriptions from digitized manuscript scans using Vision-Language models, then aggregates per-page results into a unified work-level description. It provides a FastAPI backend for integration and a React frontend for human review and editing.

> **Use case:** Support manuscript experts by pre-filling metadata and transcriptions, which are then reviewed, corrected, and finalized by humans.

## Features

- **Per-page metadata extraction** — Structured JSON with 14 fields (notation, decorations, conservation, language, layout, etc.)
- **Per-page transcription** — Faithful OCR preserving original spelling and layout
- **Work-level aggregation** — Deterministic aggregation rules combining per-page data
- **Multiple inference providers** — Local HuggingFace models (Qwen) or API (OpenAI, Google Gemini, Anthropic Claude, DeepSeek)
- **GPU-gated model selection** — CPU users are limited to small models; GPU users can access all sizes
- **Intelligent model management** — Automatic load/unload with CUDA and MPS memory cleanup
- **Human review UI** — Edit metadata and transcriptions, save changes, regenerate aggregates
- **Configurable prompts** — All extraction prompts are external `.txt` files

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- (Optional) CUDA GPU or Apple Silicon for larger models

### 1. Setup Environment
```bash
# Setup backend virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup frontend dependencies
cd frontend
npm install
cd ..

# Configure environment variables
cp .env.example .env
# Important: Edit .env to set OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY or DEEPSEEK_API_KEY if you want to use external APIs.
```

### 2. Run the Application
The easiest and most reliable way to start both the FastAPI backend and React frontend is using the included script:

```bash
chmod +x run.sh
./run.sh
```
- Frontend UI: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

Press `Ctrl+C` to stop both servers.

## Manuscript Input Structure

Each manuscript is a directory:

```
/MANUSCRIPT_NAME/
  /Immagini/           # Scanned images (jpg/png/tiff/webp)
    001_frontespizio.jpg
    002_pagina.jpg
    003_retro.jpg
  /OUTPUT/             # Created automatically by the pipeline
```

**Naming:** Image filenames must start with a 3-digit page number (e.g., `001_`, `002_`).

## Output Structure

```
/MANUSCRIPT_NAME/OUTPUT/
  /page_metadati/      # Per-page metadata JSON
    001_frontespizio.txt
    002_pagina.txt
  /Trascrizioni/       # Per-page transcription text
    001_frontespizio.txt
    002_pagina.txt
  metadata_opera.txt   # Aggregated work-level metadata JSON
  status.json          # Job status and progress
```

## API Usage

### Start an analysis

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "manuscript_path": "/path/to/manuscript",
    "mode": "both",
    "granularity": "both",
    "device": "auto",
    "provider": "openai",
    "models": {
      "vl_metadata": "",
      "vl_transcription": "",
      "text_aggregator": ""
    }
  }'
```

### Check job status

```bash
curl http://localhost:8000/jobs/{job_id}/status
```

### Edit and save metadata

```bash
# Get page metadata
curl "http://localhost:8000/pages/001_front.jpg/metadata?manuscript_path=/path/to/ms"

# Update page metadata
curl -X PUT "http://localhost:8000/pages/001_front.jpg/metadata?manuscript_path=/path/to/ms" \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"LINGUA\": \"Latino\", ...}"}'
```

### Regenerate work metadata

```bash
curl -X POST "http://localhost:8000/work/metadata/regenerate?manuscript_path=/path/to/ms&provider=openai"
```

## Prompt Files

All extraction prompts are in `prompt/`:

| File | Purpose |
|------|---------|
| `prompt_metadati.txt` | Per-page metadata extraction (VL) |
| `prompt_trascrizione.txt` | Per-page transcription/OCR (VL) |
| `prompt_aggregation_metadati.txt` | Work-level metadata aggregation (text-only) |

To customize extraction behavior, edit these files. No code changes needed.

## Models

### Vision-Language (VL)

| Model | Label | GPU Required |
|-------|-------|:---:|
| Qwen/Qwen3-VL-32B-Instruct | Slow, highest performance | ✓ |
| Qwen/Qwen3-VL-8B-Instruct | Medium, good performance (GPU default) | ✓ |
| Qwen/Qwen3-VL-4B-Instruct | Fast, medium performance | ✓ |
| Qwen/Qwen3-VL-2B-Instruct | Very fast, low performance (CPU default) | ✗ |

### Text-Only (Aggregation)

| Model | Label | GPU Required |
|-------|-------|:---:|
| Qwen/Qwen2.5-32B-Instruct | Slow, highest performance | ✓ |
| Qwen/Qwen2.5-14B-Instruct | Medium, good performance | ✓ |
| Qwen/Qwen2.5-7B-Instruct | Fast, good performance (GPU default) | ✓ |
| Qwen/Qwen2.5-3B-Instruct | Very fast, lower performance (CPU default) | ✗ |

## Hardware Notes

- **CPU only:** Only 2B (VL) and 3B (text) models are available. Larger models are disabled in both UI and API.
- **CUDA GPU:** All models available. Memory is cleaned between VL and aggregation phases.
- **Apple Silicon (MPS):** All models available. Uses `torch.mps.empty_cache()` for cleanup.
- **Device "auto":** Detects best available (CUDA > MPS > CPU).

## API Providers

When `INFERENCE_PROVIDER` is set to `openai`, `google`, `claude`, or `deepseek`, Mnemosine uses the respective external API for inference:

- **OpenAI (`openai`)**: Uses `OPENAI_API_KEY`, models via `OPENAI_VISION_MODEL` and `OPENAI_TEXT_MODEL` (default: `gpt-4o-mini`).
- **Google Gemini (`google`)**: Uses `GOOGLE_API_KEY`, models via `GOOGLE_VISION_MODEL` and `GOOGLE_TEXT_MODEL` (default: `gemini-2.5-flash`).
- **Anthropic Claude (`claude`)**: Uses `ANTHROPIC_API_KEY`, models via `CLAUDE_VISION_MODEL` and `CLAUDE_TEXT_MODEL` (default: `claude-3-5-haiku-latest`).
- **DeepSeek (`deepseek`)**: Uses `DEEPSEEK_API_KEY`, models via `DEEPSEEK_VISION_MODEL` and `DEEPSEEK_TEXT_MODEL` (default: `deepseek-chat`).

- **Cost Control:** By default, temperatures are set to `0.2` and output tokens are limited to `1200` to minimize costs.

> ⚠️ **The API providers are intended for demo/testing and may incur costs.** Monitor usage in your respective provider dashboards.

All configuration is in `.env` — no model names are hardcoded. See `.env.example` for all variables.

## 📖 API Documentation

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INFERENCE_PROVIDER` | `openai` | `hf`, `openai`, `google`, `claude`, or `deepseek` |
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `GOOGLE_API_KEY` | — | Your Google API key |
| `ANTHROPIC_API_KEY` | — | Your Anthropic (Claude) API key |
| `DEEPSEEK_API_KEY` | — | Your DeepSeek API key |
| `MANUSCRIPTS_ROOT` | `./manuscripts` | Root directory for manuscripts |
| `PROMPT_DIR` | `../prompt` | Directory containing prompt files |

## Testing

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Project Structure

```
mnemosine/
├── backend/
│   ├── app/
│   │   ├── config.py              # Settings from .env
│   │   ├── main.py                # FastAPI application
│   │   ├── model_manager.py       # Model load/unload lifecycle
│   │   ├── models_catalog.py      # Model registry + GPU gating
│   │   ├── routes/                # API endpoints
│   │   └── services/              # Pipeline, providers, utilities
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api.js                 # Backend API client
│   │   ├── App.jsx                # Main app with routing
│   │   ├── index.css              # Design system
│   │   ├── components/            # Navbar
│   │   └── pages/                 # Home, Metadata, Placeholders
│   └── package.json
├── prompt/                        # Extraction prompts (editable)
├── docs/                          # Architecture, API, formats
├── examples/                      # Dummy manuscript generator
├── .env.example
├── LICENSE
└── README.md
```

## License

MIT — see [LICENSE](LICENSE).
