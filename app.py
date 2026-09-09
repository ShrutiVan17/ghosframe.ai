import os
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.gemini_service import plan_investigation, synthesize_evidence
from services.parallel_service import search_parallel
from services.verifier import score_evidence

load_dotenv()

app = FastAPI(title="GhostFrame AI", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://shrutivan17.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VerifyRequest(BaseModel):
    claim: str
    media_url: str | None = None


OFFICIAL_CHANNELS = (
    "marvel entertainment",
    "marvel studios",
    "walt disney studios",
    "disney",
    "warner bros. pictures",
    "warner bros pictures",
    "universal pictures",
    "sony pictures entertainment",
    "paramount pictures",
    "netflix",
    "a24",
    "lionsgate movies",
)

UNOFFICIAL_CHANNELS = (
    "screen culture",
    "teaserpro",
    "stryder hd",
    "stryderhd",
    "concept trailer",
    "fan trailer",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "GhostFrame",
        "mode": "full-ai" if os.getenv("PARALLEL_API_KEY") else "provenance-fallback",
        "vertex_project_configured": bool(os.getenv("GOOGLE_CLOUD_PROJECT")),
        "parallel_configured": bool(os.getenv("PARALLEL_API_KEY")),
    }


def _youtube_metadata(url: str) -> dict:
    try:
        response = httpx.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=10,
            follow_redirects=True,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "title": data.get("title", ""),
            "author_name": data.get("author_name", ""),
            "author_url": data.get("author_url", ""),
            "thumbnail_url": data.get("thumbnail_url", ""),
        }
    except Exception:
        return {}


def _wikipedia_evidence(claim: str) -> dict | None:
    query = re.sub(
        r"(?i)\b(this|is|the|official|trailer|teaser|for|movie|film)\b",
        " ",
        claim,
    )
    query = re.sub(r"\s+", " ", query).strip(" .")
    if not query:
        return None
    try:
        response = httpx.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "utf8": 1,
                "srlimit": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
        rows = response.json().get("query", {}).get("search", [])
        if not rows:
            return None
        row = rows[0]
        snippet = re.sub("<[^>]+>", "", row.get("snippet", ""))
        title = row.get("title", query)
        return {
            "title": f"Wikipedia context — {title}",
            "url": "https://en.wikipedia.org/wiki/" + title.replace(" ", "_"),
            "excerpt": snippet,
            "source_tier": "reference",
            "stance": "neutral",
        }
    except Exception:
        return None


def fallback_verify(claim: str, media_url: str | None) -> dict:
    evidence = []
    verdict = "UNVERIFIED"
    confidence = 0.58
    support_score = 0
    contradiction_score = 0
    summary = (
        "GhostFrame could not establish official provenance from the supplied claim alone."
    )

    if media_url:
        parsed = urlparse(media_url)
        host = parsed.netloc.lower().replace("www.", "")
        meta = _youtube_metadata(media_url) if ("youtube.com" in host or "youtu.be" in host) else {}

        if meta:
            author = meta.get("author_name", "").strip()
            title = meta.get("title", "").strip()
            author_l = author.lower()
            title_l = title.lower()

            evidence.append({
                "title": title or "YouTube media metadata",
                "url": media_url,
                "excerpt": f"Published by: {author or 'Unknown channel'}. GhostFrame retrieved this directly from YouTube's public oEmbed metadata.",
                "source_tier": "platform-metadata",
                "stance": "neutral",
            })

            if any(name in author_l for name in OFFICIAL_CHANNELS):
                verdict = "SUPPORTED"
                confidence = 0.93
                support_score = 9
                contradiction_score = 1
                evidence[0]["stance"] = "support"
                evidence[0]["source_tier"] = "official-channel"
                summary = (
                    f"The submitted media resolves to a video published by “{author}”, "
                    "which matches GhostFrame's official studio/channel allowlist. "
                    "That is strong provenance evidence supporting the claim."
                )
            elif (
                any(name in author_l for name in UNOFFICIAL_CHANNELS)
                or "concept trailer" in title_l
                or "fan trailer" in title_l
                or "fan-made" in title_l
                or "unofficial" in title_l
            ):
                verdict = "LIKELY UNOFFICIAL"
                confidence = 0.95
                support_score = 1
                contradiction_score = 9
                evidence[0]["stance"] = "contradiction"
                summary = (
                    f"The submitted media is attributed to “{author}” and/or contains "
                    "concept/fan/unofficial labeling. Those provenance signals contradict "
                    "an official-studio-trailer claim."
                )
            else:
                confidence = 0.68
                summary = (
                    f"The submitted video is published by “{author or 'an unverified channel'}”. "
                    "GhostFrame could not match that publisher to a known official studio channel, "
                    "so the claim remains unverified."
                )
        else:
            evidence.append({
                "title": f"Submitted media host — {host or 'unknown'}",
                "url": media_url,
                "excerpt": "The URL was received, but public platform metadata could not be resolved.",
                "source_tier": "submitted-url",
                "stance": "neutral",
            })

    wiki = _wikipedia_evidence(claim)
    if wiki:
        evidence.append(wiki)

    plan = {
        "movie_or_franchise": claim,
        "claim_type": "media_provenance",
        "verification_questions": [
            "Who published the submitted media?",
            "Does the publisher match a known official studio or distributor channel?",
            "Does the title contain concept, fan-made, or unofficial labeling?",
            "Is there independent contextual evidence for the claimed film or franchise?",
        ],
        "search_queries": [],
    }

    analysis = {
        "summary": summary,
        "provenance_summary": (
            "Live provenance fallback: GhostFrame inspected public platform metadata, "
            "publisher identity, title-language signals, and reference context. "
            "Gemini + Parallel are used automatically when production credentials are configured."
        ),
    }

    return {
        "claim": claim,
        "media_url": media_url,
        "plan": plan,
        "evidence": evidence,
        "score": {
            "verdict": verdict,
            "confidence": confidence,
            "support_score": support_score,
            "contradiction_score": contradiction_score,
        },
        "analysis": analysis,
        "mode": "provenance-fallback",
    }


@app.post("/api/verify")
def verify(req: VerifyRequest):
    # Try the full Gemini + Parallel pipeline when both integrations are configured.
    if os.getenv("GOOGLE_CLOUD_PROJECT") and os.getenv("PARALLEL_API_KEY"):
        try:
            plan = plan_investigation(req.claim, req.media_url)
            queries = plan.get("search_queries", [])
            if not queries:
                raise ValueError("Vertex AI returned no search queries.")

            evidence = search_parallel(
                objective=(
                    "Verify whether a movie trailer or promotional-media claim is official. "
                    "Prioritize official studio/distributor sources and reputable entertainment reporting. "
                    "Also retrieve contradictory evidence when the media is concept, fan-made, unofficial, "
                    "or AI-assisted."
                ),
                queries=queries,
                max_results=10,
            )
            score = score_evidence(evidence)
            analysis = synthesize_evidence(req.claim, evidence, score)
            return {
                "claim": req.claim,
                "media_url": req.media_url,
                "plan": plan,
                "evidence": evidence,
                "score": score,
                "analysis": analysis,
                "mode": "full-ai",
            }
        except Exception:
            # Production should remain usable even if an external AI/search provider is unavailable.
            pass

    return fallback_verify(req.claim, req.media_url)


static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def home():
    return FileResponse(static_dir / "index.html")
