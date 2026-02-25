# Data Formats

## Input

### Manuscript Directory

```
/MANUSCRIPT_NAME/
  /Immagini/           # Required: scanned page images
  /OUTPUT/             # Auto-created by pipeline
```

### Image Naming

Files must start with a 3-digit page number:

```
001_frontespizio.jpg
002_pagina_interna.jpg
003_retro.jpg
```

Supported extensions: `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.webp`

## Output

### Per-Page Metadata (`OUTPUT/page_metadati/*.txt`)

JSON with exactly this structure:

```json
{
  "NOTAZIONE_MUSICALE": {
    "presenza": "SÌ|NO|\"\"",
    "tipo": "MODERNA|LETTERALE|NEUMATICA|INTAVOLATURA|QUADRATA|ALFABETO|\"\"",
    "colore_note": "string (max 30 chars)|\"\"" 
  },
  "PALINSESTO": {
    "presenza": "SÌ|NO|\"\"",
    "tipo": "INTEGRALE|PARZIALE|\"\"" 
  },
  "DECORAZIONI": {
    "iniziali_semplici": "SÌ|NO|\"\"",
    "iniziali_filigranate": "SÌ|NO|\"\"",
    "iniziali_ornate": "SÌ|NO|\"\"",
    "iniziali_istoriate": "SÌ|NO|\"\"",
    "pagine_ornate": "SÌ|NO|\"\"",
    "pagine_illustrate": "SÌ|NO|\"\""
  },
  "STATO_DI_CONSERVAZIONE": "PESSIMO|CATTIVO|DISCRETO|BUONO|OTTIMO|\"\"",
  "DESCRIZIONE_GENERALE": "string (2-4 sentences)|\"\"",
  "NOMI": "string (comma-separated)|\"\"",
  "TITOLO": "string|\"\"",
  "DATAZIONE": "ERA_CRISTIANA|ERA_BIZANTINA|...|\"\"",
  "PRESENZA_SIGILLI_TIMBRI": "SÌ|NO|\"\"",
  "STRUTTURA_MATERIALE": "FASCICOLI LEGATI|FRAMMENTO|\"\"",
  "LINGUA": "string|\"\"",
  "TIPO_PAGINA": "PAGINA_INTERNA|COPERTINA|FRONTESPIZIO|...|\"\"",
  "NOTE_ESTERNE_AL_TESTO": "SÌ|NO|\"\"",
  "IMPAGINAZIONE": "COLONNA_SINGOLA|DUE_COLONNE|TRE_COLONNE_O_PIÙ|LAYOUT_MISTO|\"\""
}
```

### Per-Page Transcription (`OUTPUT/Trascrizioni/*.txt`)

Plain text. No JSON. Faithfully transcribed text preserving:
- Original spelling, abbreviations, punctuation
- Line breaks approximately matching the original
- `[…]` for illegible portions
- Columns separated by one empty line
- Marginal notes after main text, separated by one empty line

### Work Metadata (`OUTPUT/metadata_opera.txt`)

Same JSON structure as per-page metadata, but values are aggregated across all pages using deterministic rules (see `prompt_aggregation_metadati.txt`).

### Job Status (`OUTPUT/status.json`)

```json
{
  "job_id": "abc12345",
  "manuscript_path": "/path/to/ms",
  "mode": "both",
  "granularity": "both",
  "status": "running|completed|failed|pending",
  "progress": 45.0,
  "total_pages": 10,
  "processed_pages": 4,
  "current_step": "Extracting metadata: page 5 (005_page.jpg)",
  "errors": [],
  "started_at": "2025-02-24T18:00:00+00:00",
  "completed_at": null,
  "output_paths": {}
}
```
