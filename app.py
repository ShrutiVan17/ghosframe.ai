import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from services.gemini_service import plan_investigation, synthesize
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
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "parallel_configured": bool(os.getenv("PARALLEL_API_KEY")),
    }

@app.post("/api/verify")
def verify(req: VerifyRequest):
    if not os.getenv("GEMINI_API_KEY") or not os.getenv("PARALLEL_API_KEY"):
        raise HTTPException(status_code=500, detail="Server API keys are not configured.")

    try:
        plan = plan_investigation(req.claim, req.media_url)
        queries = plan.get("search_queries", [])[:5]
        if not queries:
            raise ValueError("Gemini returned no search queries.")

        evidence = search_parallel(
            objective=(
                "Verify whether a movie trailer or promotional-media claim is official. "
                "Prioritize the official studio/distributor and reputable entertainment reporting. "
                "Also retrieve contradictory evidence if the media is a concept, fan-made, or AI-assisted trailer."
            ),
            search_queries=queries,
            max_results=10,
        )
        score = score_evidence(evidence)
        analysis = synthesize(req.claim, evidence, score)

        return {
            "claim": req.claim,
            "media_url": req.media_url,
            "plan": plan,
            "evidence": evidence,
            "score": score,
            "analysis": analysis,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Verification pipeline failed: {exc}") from exc

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def home():
    return FileResponse(static_dir / "index.html")
