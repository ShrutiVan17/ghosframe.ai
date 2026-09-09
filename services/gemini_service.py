import json
import os
from google import genai

MODEL = "gemini-2.5-flash"

def _client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def _extract_json(text: str):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned)

def plan_investigation(claim: str, media_url: str | None = None) -> dict:
    prompt = f"""
You are GhostFrame's investigation planner.
Create a concise web-verification plan for this movie-trailer authenticity claim.

CLAIM: {claim}
MEDIA URL (may be blank): {media_url or ""}

Return ONLY valid JSON with:
{{
  "movie_or_franchise": "string",
  "claim_type": "official_trailer|release_claim|studio_claim|other",
  "verification_questions": ["..."],
  "search_queries": ["..."]
}}

Rules:
- Produce 3 to 5 high-signal search queries.
- Include queries aimed at the official studio/distributor and reputable entertainment reporting.
- Include one counter-evidence query for concept/fan/AI trailer indications.
- Do not assume the claim is true or false.
"""
    response = _client().models.generate_content(model=MODEL, contents=prompt)
    return _extract_json(response.text)

def synthesize(claim: str, evidence: list[dict], score: dict) -> dict:
    compact = [
        {
            "title": e.get("title"),
            "url": e.get("url"),
            "excerpt": e.get("excerpt", "")[:900],
            "source_tier": e.get("source_tier"),
        }
        for e in evidence[:12]
    ]
    prompt = f"""
You are GhostFrame's evidence analyst. Analyze only the supplied evidence.
Do not invent sources, facts, dates, or quotes.

CLAIM: {claim}
DETERMINISTIC SCORE: {json.dumps(score)}
EVIDENCE: {json.dumps(compact)}

Return ONLY valid JSON:
{{
  "summary": "2-4 sentence grounded explanation",
  "supporting_points": ["..."],
  "contradictions": ["..."],
  "uncertainties": ["..."],
  "recommended_next_check": "..."
}}
"""
    response = _client().models.generate_content(model=MODEL, contents=prompt)
    return _extract_json(response.text)
