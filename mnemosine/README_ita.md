# Mnemosine

**Analisi automatizzata di manoscritti per il Ministero della Cultura (MiC).**

Mnemosine estrae metadati strutturati e trascrizioni da scansioni digitalizzate di manoscritti utilizzando modelli Vision-Language, aggregando poi i risultati per-pagina in una descrizione unificata dell'opera. Il sistema fornisce un backend FastAPI per l'integrazione e un frontend React per la revisione e la modifica umana.

> **Caso d'uso:** Supportare gli esperti di manoscritti nella precompilazione di metadati e trascrizioni, che vengono poi rivisti, corretti e finalizzati dagli operatori.

## Funzionalità

- **Estrazione metadati per pagina** — JSON strutturato con 14 campi (notazione, decorazioni, conservazione, lingua, impaginazione, ecc.)
- **Trascrizione per pagina** — OCR fedele che preserva grafia originale e layout
- **Aggregazione a livello di opera** — Regole deterministiche per combinare dati per-pagina
- **Due provider di inferenza** — Modelli HuggingFace locali (Qwen) o API OpenAI
- **Selezione modelli con gating GPU** — Utenti CPU limitati ai modelli piccoli; GPU abilitata per tutti
- **Gestione intelligente modelli** — Caricamento/scaricamento automatico con pulizia memoria CUDA e MPS
- **UI per revisione umana** — Modifica metadati e trascrizioni, salva, rigenera aggregati
- **Prompt configurabili** — Tutti i prompt di estrazione sono file `.txt` esterni

## Avvio Rapido

### Prerequisiti

- Python 3.10+
- Node.js 18+ (per il frontend)
- (Opzionale) GPU CUDA o Apple Silicon per modelli più grandi

### 1. Preparazione dell'Ambiente
```bash
# Setup ambiente virtuale backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup dipendenze frontend
cd frontend
npm install
cd ..

# Configurazione variabili d'ambiente
cp .env.example .env
# Importante: Modifica .env per impostare OPENAI_API_KEY se desideri usare le API OpenAI.
```

### 2. Esecuzione dell'Applicazione
Il modo più semplice e affidabile per avviare il backend FastAPI e il frontend React è utilizzare lo script incluso:

```bash
chmod +x run.sh
./run.sh
```
- Interfaccia UI: `http://localhost:5173`
- API Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

Premi `Ctrl+C` nel terminale per fermare entrambi i server.

## Struttura Input Manoscritto

Ogni manoscritto è una directory:

```
/NOME_MANOSCRITTO/
  /Immagini/           # Immagini scansionate (jpg/png/tiff/webp)
    001_frontespizio.jpg
    002_pagina.jpg
    003_retro.jpg
  /OUTPUT/             # Creata automaticamente dalla pipeline
```

**Nomenclatura:** I nomi dei file immagine devono iniziare con un numero di 3 cifre (es. `001_`, `002_`).

## Struttura Output

```
/NOME_MANOSCRITTO/OUTPUT/
  /page_metadati/      # Metadati JSON per-pagina
    001_frontespizio.txt
    002_pagina.txt
  /Trascrizioni/       # Trascrizione testuale per-pagina
    001_frontespizio.txt
    002_pagina.txt
  metadata_opera.txt   # Metadati aggregati dell'opera (JSON)
  status.json          # Stato e avanzamento del job
```

## Uso API

### Avviare un'analisi

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "manuscript_path": "/percorso/al/manoscritto",
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

### Controllare lo stato del job

```bash
curl http://localhost:8000/jobs/{job_id}/status
```

### Modificare e salvare metadati

```bash
# Ottenere metadati pagina
curl "http://localhost:8000/pages/001_front.jpg/metadata?manuscript_path=/percorso/ms"

# Aggiornare metadati pagina
curl -X PUT "http://localhost:8000/pages/001_front.jpg/metadata?manuscript_path=/percorso/ms" \
  -H "Content-Type: application/json" \
  -d '{"content": "{\"LINGUA\": \"Latino\", ...}"}'
```

### Rigenerare metadati opera

```bash
curl -X POST "http://localhost:8000/work/metadata/regenerate?manuscript_path=/percorso/ms&provider=openai"
```

## File Prompt

Tutti i prompt di estrazione sono in `prompt/`:

| File | Scopo |
|------|-------|
| `prompt_metadati.txt` | Estrazione metadati per-pagina (VL) |
| `prompt_trascrizione.txt` | Trascrizione/OCR per-pagina (VL) |
| `prompt_aggregation_metadati.txt` | Aggregazione metadati a livello di opera (text-only) |

Per personalizzare il comportamento dell'estrazione, modificare questi file. Non è necessario cambiare il codice.

## Modelli

### Vision-Language (VL)

| Modello | Descrizione | Richiede GPU |
|---------|-------------|:---:|
| Qwen/Qwen3-VL-32B-Instruct | Lento, massime prestazioni | ✓ |
| Qwen/Qwen3-VL-8B-Instruct | Medio, buone prestazioni (default GPU) | ✓ |
| Qwen/Qwen3-VL-4B-Instruct | Veloce, prestazioni medie | ✓ |
| Qwen/Qwen3-VL-2B-Instruct | Molto veloce, prestazioni basse (default CPU) | ✗ |

### Text-Only (Aggregazione)

| Modello | Descrizione | Richiede GPU |
|---------|-------------|:---:|
| Qwen/Qwen2.5-32B-Instruct | Lento, massime prestazioni | ✓ |
| Qwen/Qwen2.5-14B-Instruct | Medio, buone prestazioni | ✓ |
| Qwen/Qwen2.5-7B-Instruct | Veloce, buone prestazioni (default GPU) | ✓ |
| Qwen/Qwen2.5-3B-Instruct | Molto veloce, prestazioni inferiori (default CPU) | ✗ |

## Note Hardware

- **Solo CPU:** Disponibili solo modelli 2B (VL) e 3B (text). I modelli più grandi sono disabilitati nell'UI e nell'API.
- **GPU CUDA:** Tutti i modelli disponibili. La memoria viene pulita tra la fase VL e l'aggregazione.
- **Apple Silicon (MPS):** Tutti i modelli disponibili. Usa `torch.mps.empty_cache()` per la pulizia.
- **Device "auto":** Rileva automaticamente il migliore (CUDA > MPS > CPU).

## Provider OpenAI

Quando `INFERENCE_PROVIDER=openai`, Mnemosine utilizza le API OpenAI per l'inferenza:

- **Modello vision:** Configurabile via `OPENAI_VISION_MODEL` (default: `gpt-4o-mini`)
- **Modello text:** Configurabile via `OPENAI_TEXT_MODEL` (default: `gpt-4o-mini`)
- **Costi:** Temperatura bassa (0.2) e token di output limitati (1200) minimizzano i costi

> ⚠️ **Il provider OpenAI è pensato per demo/test e può generare costi.** Monitorare l'utilizzo nella dashboard OpenAI.

Tutta la configurazione è nel file `.env` — nessun nome di modello è hardcodato. Vedere `.env.example` per tutte le variabili.

## Variabili d'Ambiente

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `INFERENCE_PROVIDER` | `openai` | `hf` (locale) o `openai` (API) |
| `OPENAI_API_KEY` | — | La tua chiave API OpenAI |
| `OPENAI_VISION_MODEL` | `gpt-4o-mini` | Modello OpenAI per task vision |
| `OPENAI_TEXT_MODEL` | `gpt-4o-mini` | Modello OpenAI per task testo |
| `OPENAI_TEMPERATURE` | `0.2` | Temperatura per la generazione |
| `OPENAI_MAX_OUTPUT_TOKENS` | `1200` | Max token per risposta |
| `MANUSCRIPTS_ROOT` | `./manuscripts` | Directory root dei manoscritti |
| `PROMPT_DIR` | `../prompt` | Directory contenente i file prompt |

## Test

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Licenza

MIT — vedi [LICENSE](LICENSE).
