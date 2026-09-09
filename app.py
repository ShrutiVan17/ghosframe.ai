import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.gemini_service import plan_investigation, synthesize_evidence
from services.parallel_service import search_parallel
from services.verifier import score_evidence

load_dotenv()

app = FastAPI(title="GhostFrame AI", version="1.0.0")

class VerifyRequest(BaseModel):
    claim: str
    media_url: str | None = None

@app.get("/health")
def health():
    return {
        "status": "ok",
        "vertex_project_configured": bool(os.getenv("GOOGLE_CLOUD_PROJECT")),
        "vertex_location": os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
        "parallel_configured": bool(os.getenv("PARALLEL_API_KEY")),
    }

@app.post("/api/verify")
def verify(req: VerifyRequest):
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        raise HTTPException(status_code=500, detail="GOOGLE_CLOUD_PROJECT is not configured.")
    if not os.getenv("PARALLEL_API_KEY"):
        raise HTTPException(status_code=500, detail="PARALLEL_API_KEY is not configured.")

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

        analysis = synthesize_evidence(
            req.claim,
            evidence,
            score,
        )

        return {
            "claim": req.claim,
            "media_url": req.media_url,
            "plan": plan,
            "evidence": evidence,
            "score": score,
            "analysis": analysis,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Verification pipeline failed: {exc}",
        ) from exc

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def home():
    return FileResponse(static_dir / "index.html")
