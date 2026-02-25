# UI Documentation

## Overview

Mnemosine's frontend is a single-page React application built with Vite. It provides a clean, modern interface with violet/lilac accents following the institutional design aesthetic.

## Design System

The UI is built on a CSS-variable-based design system defined in `index.css`:

- **Color palette:** Violet primary (#8878E8), lavender accents, light neutrals
- **Typography:** Inter (Google Fonts), with weight hierarchy 400–700
- **Components:** Pill buttons, rounded cards (16px radius), bordered inputs
- **Spacing:** 8px base unit
- **Icons:** Lucide React (outline, stroke 1.5–2)

See `docs/UI_STYLE_GUIDE.md` for the full style specification.

## Pages

### Home (`/`)

Hero section with gradient background, project description, and two CTA buttons. Below: 4 feature cards showcasing Metadata Extraction, Transcription, Work Aggregation, and Human Review.

### Metadata (`/metadata`)

The main working page, split into:

**Sidebar (320px)**
- Manuscript directory browser (dropdown or manual path input)
- Configuration: Provider, Device, Mode, Granularity
- Model dropdowns (HF only) with GPU gating
- "Start Analysis" button

**Main Panel**
- Job progress bar with status
- Tabbed view: Metadata | Transcription | Work Metadata
- Page list with status dots (green = available, gray = pending)
- Editor area for selected page content
- Save button (updates file on disk)
- Regenerate button (for stale work metadata)

### XML Parser, Retrieve, RAG (`/xml-parser`, `/retrieve`, `/rag`)

Placeholder pages with consistent styling. Marked as "under development."

## API Integration

The frontend communicates with the backend via `api.js`:
- All API calls target `http://localhost:8000` (configurable)
- `GET /models/catalog` populates model dropdowns
- `POST /analyze` starts jobs; polling via `GET /jobs/{id}/status`
- CRUD endpoints for saving edits

## OpenAI Provider UX

When `provider=openai`:
- A warning badge appears: "OpenAI (demo) — May incur costs"
- Model dropdowns are hidden (OpenAI models come from env)
- HF model IDs are not sent to the API
