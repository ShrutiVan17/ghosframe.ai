# GhostFrame Architecture

```mermaid
flowchart LR
    U["User Claim / Trailer URL"] --> API["FastAPI Orchestrator"]
    API --> G1["Gemini 2.5 Flash\nInvestigation Planner"]
    G1 --> P["Parallel Search API\nLive Web Evidence"]
    P --> N["Evidence Normalizer"]
    N --> S["Deterministic Scoring"]
    N --> G2["Gemini 2.5 Flash\nEvidence Analyst"]
    S --> V["Verdict Engine"]
    G2 --> V
    V --> UI["Cinematic Evidence Console"]
```

## Design principles
- Gemini reasons, but does not invent the score.
- Parallel provides live evidence.
- Python produces the final support/contradiction score.
- API keys never reach the browser.
- No Vertex AI authentication is required.
