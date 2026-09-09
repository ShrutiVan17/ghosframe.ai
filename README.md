# GhostFrame AI

GhostFrame is an agentic media-verification app that investigates whether a movie trailer presented as "official" is actually supported by public evidence.

## Stack
- Gemini Developer API (`gemini-2.5-flash`)
- Parallel Search API
- FastAPI
- Vanilla HTML/CSS/JS

## Free-tier setup
This project intentionally avoids Vertex AI authentication.

Create `.env`:
```env
GEMINI_API_KEY=your_existing_key
PARALLEL_API_KEY=your_existing_key
```

Do not commit `.env`.

## Install
```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Test both keys
```bash
python auth_test.py
```

Expected:
```text
Gemini authentication passed
Parallel authentication passed
```

## Run
```bash
uvicorn app:app --reload --port 8080
```

Open:
```text
http://localhost:8080
```

## Example claim
```text
This is the official trailer for Avengers: Secret Wars.
```

## Important
GhostFrame does not simply ask whether AI was used. It asks whether the claimed identity and context of the media are supported by evidence.
