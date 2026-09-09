# GhostFrame AI

**Agentic authenticity verification for movie trailers**

GhostFrame investigates whether a movie trailer presented as “official” is actually supported by public evidence. Gemini plans the investigation and reasons over evidence; Parallel Search retrieves live web evidence; a deterministic scoring layer produces an explainable verdict.

## Why it matters
AI-assisted and fan-made trailers can look like studio releases. GhostFrame does not merely ask “was AI used?” It asks a more useful question: **is the claim being made about this media supported by evidence?**

## Core flow
1. User submits a trailer URL/title and claim.
2. Gemini converts the claim into verification questions and search queries.
3. Parallel Search retrieves live evidence from the public web.
4. GhostFrame normalizes sources and looks for studio confirmation, reputable reporting, contradictory evidence, and provenance clues.
5. Gemini synthesizes a grounded explanation.
6. A deterministic evidence score returns **SUPPORTED**, **UNVERIFIED**, or **LIKELY UNOFFICIAL**.

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md).

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your existing keys in `.env`:
```
GEMINI_API_KEY=your_existing_key
PARALLEL_API_KEY=your_existing_key
```

Never commit `.env`.

## Authentication gate
Run this before the app:
```bash
python auth_test.py
```
The test uses the Gemini Developer API with `gemini-2.5-flash` and a minimal Parallel Search request. It does not use Vertex AI.

## Run
```bash
uvicorn app:app --reload --port 8080
```
Open http://localhost:8080

## Cloud Run
```bash
gcloud run deploy ghostframe-ai --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="$GEMINI_API_KEY",PARALLEL_API_KEY="$PARALLEL_API_KEY" \
  --min 0 --max 1 --memory 512Mi --cpu 1
```

## Hackathon demo
Use a claim like:
> “This is the official trailer for [movie title].”

GhostFrame will:
- generate verification queries,
- search official and reputable sources,
- surface supporting/contradictory evidence,
- show an evidence trail,
- return an explainable verdict.

## Security
API keys are read only from environment variables and are never returned to the browser.

## Data / claims
GhostFrame is an evidence assistant, not a forensic guarantee. A verdict reflects the evidence retrieved at query time and should be read with the displayed sources.

## License
MIT
