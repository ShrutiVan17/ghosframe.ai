import os
import sys
import httpx
from dotenv import load_dotenv
from google import genai

MODEL = "gemini-2.5-flash"

def vertex_client():
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    return genai.Client(
        vertexai=True,
        project=project,
        location=location,
    )

def test_vertex():
    client = vertex_client()
    response = client.models.generate_content(
        model=MODEL,
        contents="Reply only with: GhostFrame Vertex AI is working",
    )
    text = (response.text or "").strip()
    if text != "GhostFrame Vertex AI is working":
        raise RuntimeError(f"Unexpected Vertex AI response: {text}")

def test_parallel():
    headers = {
        "Content-Type": "application/json",
        "x-api-key": os.environ["PARALLEL_API_KEY"],
    }
    payload = {
        "mode": "fast",
        "objective": "Authentication test. Find the official Parallel website.",
        "search_queries": ["Parallel official website"],
        "advanced_settings": {
            "max_results": 1
        },
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.parallel.ai/v1/search",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

def main():
    load_dotenv(override=True)

    missing = [
        name for name in ("GOOGLE_CLOUD_PROJECT", "PARALLEL_API_KEY")
        if not os.getenv(name)
    ]
    if missing:
        print("Missing environment variable(s): " + ", ".join(missing))
        sys.exit(1)

    try:
        test_vertex()
        print("Vertex AI authentication passed")
    except Exception as exc:
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        code = getattr(exc, "code", None)
        msg = getattr(exc, "message", None) or str(exc)
        print(f"HTTP status: {status}")
        print(f"Google API error code: {code}")
        print(f"model name: {MODEL}")
        print(f"Vertex AI error message: {msg}")
        sys.exit(1)

    try:
        test_parallel()
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
