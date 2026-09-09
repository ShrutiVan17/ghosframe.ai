import os
import httpx

PARALLEL_URL = "https://api.parallel.ai/v1/search"

def search_parallel(objective: str, queries: list[str], max_results: int = 10) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.environ["PARALLEL_API_KEY"],
    }

    payload = {
        "mode": "fast",
        "objective": objective,
        "search_queries": queries[:5],
        "advanced_settings": {
            "max_results": max_results
        },
    }

    with httpx.Client(timeout=45.0) as client:
        response = client.post(PARALLEL_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    raw = (
        data.get("results")
        or data.get("search_results")
        or data.get("data")
        or []
    )

    normalized = []
    for item in raw:
        normalized.append({
            "title": item.get("title") or item.get("name") or "Untitled source",
            "url": item.get("url") or item.get("source_url") or "",
            "excerpt": (
                item.get("excerpt")
                or item.get("content")
                or item.get("text")
                or item.get("description")
                or ""
            ),
        })
    return normalized
