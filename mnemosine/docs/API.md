# API Reference

Base URL: `http://localhost:8000`

## Health

### GET /health

```json
{ "status": "ok", "service": "mnemosine" }
```

## Models

### GET /models/catalog

Returns available models with GPU availability info.

**Response:**
```json
{
  "models": [
    {
      "id": "Qwen/Qwen3-VL-8B-Instruct",
      "type": "vl",
      "label": "Medium, good performance (GPU default)",
      "requires_gpu": true
    }
  ],
  "gpu_available": false,
  "detected_device": "cpu",
  "recommended_device": "auto",
  "defaults": {
    "vl": "Qwen/Qwen3-VL-2B-Instruct",
    "text": "Qwen/Qwen2.5-3B-Instruct"
  }
}
```

## Analysis

### POST /analyze

Start an analysis pipeline job.

**Body:**
```json
{
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
}
```

| Field | Values | Default |
|-------|--------|---------|
| `mode` | `metadata`, `transcription`, `both` | `both` |
| `granularity` | `page`, `work`, `both` | `both` |
| `device` | `auto`, `cpu`, `cuda`, `mps` | `auto` |
| `provider` | `hf`, `openai` | `openai` |

**Response:** `{ "job_id": "abc12345" }`

**Errors:**
- `400` — Invalid path, GPU-only model on CPU
- `409` — Another pipeline is already running

### GET /jobs/{job_id}/status

**Response:**
```json
{
  "job_id": "abc12345",
  "status": "running",
  "progress": 45.0,
  "total_pages": 10,
  "processed_pages": 4,
  "current_step": "Extracting metadata: page 5",
  "errors": [],
  "started_at": "2025-02-24T18:00:00Z",
  "completed_at": null
}
```

### GET /jobs/{job_id}/results

Returns full job info after completion.

## Manuscripts

### GET /manuscripts/browse?path=...

List manuscript directories.

**Response:**
```json
{
  "manuscripts": [
    { "name": "ms_001", "path": "/data/ms_001", "has_images": true, "has_output": true }
  ],
  "current_path": "/data"
}
```

### GET /pages?manuscript_path=...

List pages with metadata/transcription availability.

**Response:**
```json
[
  { "page_number": 1, "filename": "001_front.jpg", "has_metadata": true, "has_transcription": false }
]
```

### GET /pages/{filename}/metadata?manuscript_path=...

Get page metadata JSON.

### PUT /pages/{filename}/metadata?manuscript_path=...

Update page metadata. Body: `{ "content": "..." }`. Marks work metadata as stale.

### GET /pages/{filename}/transcription?manuscript_path=...

Get page transcription text.

### PUT /pages/{filename}/transcription?manuscript_path=...

Update page transcription. Body: `{ "content": "..." }`.

### GET /pages/{filename}/image?manuscript_path=...

Serve the page image file.

### GET /work/metadata?manuscript_path=...

Get aggregated work metadata. Includes `is_stale` flag.

### POST /work/metadata/regenerate?manuscript_path=...&provider=openai&device=auto

Regenerate work metadata from current per-page metadata files.
