"""Live smoke test for the deployed HireSense API (run by GitHub Actions).

Waits for a cold start (Render free services sleep after 15 idle minutes),
then checks /health and runs one real CV-to-job match. Exits non-zero on
failure so the workflow can open an alert issue. Standard library only.

    python scripts/smoke_test.py https://hiresense-ai-3k4d.onrender.com
"""
import json
import sys
import time
import urllib.error
import urllib.request

CV = ("Machine Learning Engineer. Built a RAG system in Python with FAISS and "
      "Sentence Transformers. Deployed FastAPI services with Docker on GCP.")
JD = ("We need a Python engineer with NLP and LLM experience. You will deploy "
      "services on AWS with Docker and Kubernetes.")


def request(url, payload=None, timeout=90):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json",
                                                          "User-Agent": "hiresense-smoke-test"})
    start = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read()), time.time() - start


def wait_for_health(base, deadline_s=300):
    start = time.time()
    last = None
    while time.time() - start < deadline_s:
        try:
            status, body, _ = request(f"{base}/health")
            if status == 200 and body.get("status") == "ok":
                return body, time.time() - start
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last = e
        time.sleep(10)
    raise SystemExit(f"FAIL /health not ok after {deadline_s}s (last error: {last})")


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else "https://hiresense-ai-3k4d.onrender.com").rstrip("/")
    health, waited = wait_for_health(base)
    print(f"OK   /health after {waited:.0f}s: {health}")

    # The embedding model loads in the background after start-up; give it time.
    for attempt in range(6):
        status, body, secs = request(f"{base}/api/match", {"resume_text": CV, "job_description": JD})
        if status != 200:
            raise SystemExit(f"FAIL /api/match returned {status}")
        if body.get("method") == "embeddings" or attempt == 5:
            break
        print(f"...  matcher method={body.get('method')}, waiting for embeddings")
        time.sleep(20)

    problems = []
    if not 0 <= body.get("match_score", -1) <= 100:
        problems.append(f"match_score out of range: {body.get('match_score')}")
    if not {"python", "docker"} <= set(body.get("matched_skills", [])):
        problems.append(f"expected python+docker matched, got {body.get('matched_skills')}")
    if "kubernetes" not in body.get("missing_skills", []):
        problems.append(f"expected kubernetes missing, got {body.get('missing_skills')}")
    if problems:
        raise SystemExit("FAIL /api/match: " + "; ".join(problems))
    print(f"OK   /api/match in {secs:.1f}s: score={body['match_score']} method={body.get('method')}")
    if body.get("method") != "embeddings":
        print("WARN matcher still on the lexical fallback")


if __name__ == "__main__":
    main()
