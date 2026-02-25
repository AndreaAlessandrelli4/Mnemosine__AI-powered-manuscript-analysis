# Mnemosine

## Development Setup

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # Edit with your config
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Code Style
- Python: follow PEP 8
- JavaScript/React: use consistent formatting (Prettier recommended)
- Write docstrings for all public functions

## Prompt Files
Prompt files in `prompt/` are domain-specific and reviewed by manuscript experts. Changes to prompts should include a rationale and be tested against sample manuscripts.
