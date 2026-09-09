from urllib.parse import urlparse

OFFICIAL_HINTS = (
    "disney.com", "marvel.com", "warnerbros.com", "paramount.com",
    "universalpictures.com", "sonypictures.com", "netflix.com",
)
REPUTABLE_HINTS = (
    "variety.com", "hollywoodreporter.com", "deadline.com",
    "reuters.com", "apnews.com",
)
UNOFFICIAL_TERMS = (
    "concept trailer", "fan trailer", "fan-made", "fan made",
    "ai trailer", "unofficial trailer", "parody",
)
OFFICIAL_TERMS = (
    "official trailer", "official teaser", "studio released",
    "released the trailer", "debuted the trailer",
)

def source_tier(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if any(h in host for h in OFFICIAL_HINTS):
        return "official"
    if any(h in host for h in REPUTABLE_HINTS):
        return "reputable"
    return "web"

def score_evidence(evidence: list[dict]) -> dict:
    support = 0
    contradiction = 0

    for e in evidence:
        e["source_tier"] = source_tier(e.get("url", ""))
        text = f"{e.get('title','')} {e.get('excerpt','')}".lower()
        tier = e["source_tier"]
        weight = 5 if tier == "official" else 3 if tier == "reputable" else 1

        if any(term in text for term in OFFICIAL_TERMS):
            support += weight
        if any(term in text for term in UNOFFICIAL_TERMS):
            contradiction += weight

    total = max(1, support + contradiction)
    official_ratio = support / total

    if contradiction >= support + 3:
        verdict = "LIKELY UNOFFICIAL"
    elif support >= contradiction + 4 and support >= 5:
        verdict = "SUPPORTED"
    else:
        verdict = "UNVERIFIED"

    confidence = round(min(0.96, 0.52 + abs(support - contradiction) / max(10, total) * 0.44), 2)

    return {
        "verdict": verdict,
        "confidence": confidence,
        "support_score": support,
        "contradiction_score": contradiction,
        "official_support_ratio": round(official_ratio, 2),
    }
