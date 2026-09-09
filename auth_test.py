import os
import sys
import httpx
from dotenv import load_dotenv
from google import genai

MODEL = "gemini-2.5-flash"

def gemini_test():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=MODEL,
        contents="Reply only with: GhostFrame Gemini is working",
    )
    text = (response.text or "").strip()
    if "GhostFrame Gemini is working" not in text:
        raise RuntimeError(f"Unexpected Gemini response for model {MODEL}")
    return True

def parallel_test():
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.environ["PARALLEL_API_KEY"],
        "parallel-beta": "search-extract-2025-10-10",
    }
    payload = {
        "objective": "Authentication test. Find the official website for Parallel.",
        "search_queries": ["Parallel official website"],
        "max_results": 1,
        "max_chars_per_result": 300,
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post("https://api.parallel.ai/v1beta/search", headers=headers, json=payload)
        response.raise_for_status()
    return True

def main():
    load_dotenv(override=True)
    missing = [k for k in ("GEMINI_API_KEY", "PARALLEL_API_KEY") if not os.getenv(k)]
    if missing:
        print("Missing environment variable(s): " + ", ".join(missing))
        sys.exit(1)

    try:
        gemini_test()
        print("Gemini authentication passed")
    except Exception as exc:
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        api_code = getattr(exc, "code", None)
        message = getattr(exc, "message", None) or str(exc)
        print(f"HTTP status: {status}")
        print(f"Google API error code: {api_code}")
        print(f"model name: {MODEL}")
        print(f"exact billing/tier error message: {message}")
        sys.exit(1)

    try:
        parallel_test()
        print("Parallel authentication passed")
    except httpx.HTTPStatusError as exc:
        print(f"Parallel HTTP status: {exc.response.status_code}")
        print(f"Parallel error: {exc.response.text}")
        sys.exit(1)
    except Exception as exc:
        print(f"Parallel error: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
