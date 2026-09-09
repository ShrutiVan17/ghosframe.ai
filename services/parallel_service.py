import os
import httpx

PARALLEL_URL = "https://api.parallel.ai/v1beta/search"

def search_parallel(objective: str, search_queries: list[str], max_results: int = 8) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.environ["PARALLEL_API_KEY"],
        "parallel-beta": "search-extract-2025-10-10",
    }
    payload = {
        "objective": objective,
        "search_queries": search_queries[:5],
        "max_results": max_results,
        "max_chars_per_result": 2500,
    }

    with httpx.Client(timeout=45.0) as client:
        response = client.post(PARALLEL_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    raw_results = data.get("results") or data.get("search_results") or []
    normalized = []
    for item in raw_results:
        normalized.append({
            "title": item.get("title") or item.get("name") or "Untitled source",
            "url": item.get("url") or item.get("source_url") or "",
            "excerpt": item.get("excerpt") or item.get("content") or item.get("text") or "",
        })
    return normalized
