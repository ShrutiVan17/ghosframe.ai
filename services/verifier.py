from urllib.parse import urlparse

OFFICIAL_HOST_HINTS = (
    "marvel.com",
    "disney.com",
    "warnerbros.com",
    "paramount.com",
    "universalpictures.com",
    "sonypictures.com",
    "netflix.com",
    "a24films.com",
)

REPUTABLE_HOST_HINTS = (
    "variety.com",
    "hollywoodreporter.com",
    "deadline.com",
    "reuters.com",
    "apnews.com",
    "entertainmentweekly.com",
)

UNOFFICIAL_TERMS = (
    "concept trailer",
    "fan trailer",
    "fan-made",
    "fan made",
    "unofficial trailer",
    "ai trailer",
    "ai-generated",
    "ai generated",
    "parody trailer",
)

OFFICIAL_TERMS = (
    "official trailer",
    "official teaser",
    "released the trailer",
    "debuted the trailer",
    "studio released",
)

def source_tier(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if any(hint in host for hint in OFFICIAL_HOST_HINTS):
        return "official"
    if any(hint in host for hint in REPUTABLE_HOST_HINTS):
        return "reputable"
    return "web"

def score_evidence(evidence: list[dict]) -> dict:
    support = 0
    contradiction = 0

    for e in evidence:
        tier = source_tier(e.get("url", ""))
        e["source_tier"] = tier

        text = f"{e.get('title','')} {e.get('excerpt','')}".lower()
        weight = 5 if tier == "official" else 3 if tier == "reputable" else 1

        has_support = any(term in text for term in OFFICIAL_TERMS)
        has_contra = any(term in text for term in UNOFFICIAL_TERMS)

        if has_support:
            support += weight
        if has_contra:
            contradiction += weight

        if has_support and not has_contra:
            e["stance"] = "support"
        elif has_contra and not has_support:
            e["stance"] = "contradiction"
        else:
            e["stance"] = "neutral"

    total = max(1, support + contradiction)

    if contradiction >= support + 3:
        verdict = "LIKELY UNOFFICIAL"
    elif support >= contradiction + 4 and support >= 5:
        verdict = "SUPPORTED"
    else:
        verdict = "UNVERIFIED"

    confidence = round(
        min(0.96, 0.52 + abs(support - contradiction) / max(10, total) * 0.44),
        2,
    )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "support_score": support,
        "contradiction_score": contradiction,
    }
