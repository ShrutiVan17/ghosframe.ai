# GhostFrame AI

GhostFrame is an agentic media-verification app that investigates whether a movie trailer presented as "official" is actually supported by public evidence.

## Stack
- Vertex AI Gemini (`gemini-2.5-flash`)
- Parallel Search API
- FastAPI
- Vanilla HTML/CSS/JS

## Authentication
GhostFrame now uses **Vertex AI with Application Default Credentials (ADC)** instead of a Gemini API key.

You need:
- a Google Cloud project with Vertex AI API enabled
- `GOOGLE_CLOUD_PROJECT`
- optional `GOOGLE_CLOUD_LOCATION` (defaults to `global`)
- your existing `PARALLEL_API_KEY`

Create `.env`:
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
PARALLEL_API_KEY=your-existing-parallel-key
```

Do not commit `.env`.

## Local authentication
Install Google Cloud CLI, then:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com
```

Then install:

```bash
pip install -r requirements.txt
```

## Test Vertex AI + Parallel
```bash
python auth_test.py
```

Expected:

```text
Vertex AI authentication passed
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
