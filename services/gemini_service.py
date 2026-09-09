import json
import os
from google import genai

MODEL = "gemini-2.5-flash"

def _client():
    return genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
    )

def _clean_json(text: str):
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned)

def plan_investigation(claim: str, media_url: str | None = None) -> dict:
    prompt = f"""
You are GhostFrame's investigation planner.

Investigate whether a movie trailer or promotional-media claim is actually supported by public evidence.

CLAIM:
{claim}

MEDIA URL:
{media_url or ""}

Return ONLY valid JSON:
{{
  "movie_or_franchise": "string",
  "claim_type": "official_trailer|official_teaser|release_claim|studio_claim|other",
  "verification_questions": ["question 1", "question 2", "question 3", "question 4"],
  "search_queries": ["query 1", "query 2", "query 3", "query 4"]
}}

Rules:
- Do not assume the claim is true or false.
- Include at least one official-studio-focused query.
- Include at least one reputable entertainment-news query.
- Include at least one counter-evidence query for concept/fan-made/AI-assisted trailer indications.
- Do not invent sources.
"""
    client = _client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return _clean_json(response.text)

def synthesize_evidence(claim: str, evidence: list[dict], score: dict) -> dict:
    compact = [
        {
            "title": e.get("title"),
            "url": e.get("url"),
            "excerpt": (e.get("excerpt") or "")[:1000],
            "source_tier": e.get("source_tier"),
            "stance": e.get("stance"),
        }
        for e in evidence[:12]
    ]

    prompt = f"""
You are GhostFrame's evidence analyst.

Use ONLY the supplied evidence.
Do not invent URLs, dates, announcements, quotes, or facts.

CLAIM:
{claim}

DETERMINISTIC SCORE:
{json.dumps(score)}

EVIDENCE:
{json.dumps(compact)}

Return ONLY valid JSON:
{{
  "summary": "2-4 sentence grounded explanation",
  "supporting_points": ["..."],
  "contradictions": ["..."],
  "uncertainties": ["..."],
  "provenance_summary": "...",
  "recommended_next_check": "..."
}}
"""
    client = _client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return _clean_json(response.text)
