"""API tests (run: pytest -q). Uses in-memory demo accounts, no Firebase needed."""
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register(password="correct-horse-1"):
    email = f"t{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": password, "name": "Test User"})
    assert r.status_code == 200, r.text
    return email, r.json()


def test_register_login_and_profile():
    email, reg = _register()
    assert reg["name"] == "Test User" and reg["access_token"]
    r = client.post("/api/auth/login", json={"email": email, "password": "correct-horse-1"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    prof = client.get("/api/profile", headers={"Authorization": f"Bearer {token}"})
    assert prof.status_code == 200 and prof.json()["email"] == email


def test_wrong_password_and_unknown_user_rejected():
    email, _ = _register()
    assert client.post("/api/auth/login", json={"email": email, "password": "wrong-password"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x" * 10}).status_code == 401


def test_duplicate_email_rejected():
    email, _ = _register()
    r = client.post("/api/auth/register", json={"email": email, "password": "another-pass-1", "name": "X"})
    assert r.status_code == 400


def test_short_password_rejected():
    r = client.post("/api/auth/register", json={"email": "a@example.com", "password": "short", "name": "A"})
    assert r.status_code == 422


def test_protected_routes_need_a_valid_token():
    assert client.get("/api/profile").status_code == 401
    assert client.get("/api/profile", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    assert client.get("/api/applications").status_code == 401


def test_match_endpoint():
    cv = ("Machine Learning Engineer. Built a RAG system in Python with FAISS and Sentence Transformers. "
          "Deployed FastAPI services with Docker on GCP.")
    jd = ("We need a Python engineer with NLP and LLM experience. "
          "You will deploy services on AWS with Docker and Kubernetes.")
    r = client.post("/api/match", json={"resume_text": cv, "job_description": jd})
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["match_score"] <= 100
    assert {"python", "docker"} <= set(body["matched_skills"])
    assert "kubernetes" in body["missing_skills"]


def test_match_rejects_tiny_inputs():
    assert client.post("/api/match", json={"resume_text": "hi", "job_description": "x" * 60}).status_code == 422


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_match_file_txt_and_docx():
    jd = ("We need a Python engineer with NLP and LLM experience. "
          "You will deploy services on AWS with Docker and Kubernetes.")
    cv = ("Machine Learning Engineer. Built a RAG system in Python with FAISS and Sentence Transformers. "
          "Deployed FastAPI services with Docker on GCP.")
    r = client.post("/api/match/file", data={"job_description": jd},
                    files={"file": ("cv.txt", cv.encode(), "text/plain")})
    assert r.status_code == 200 and "python" in r.json()["matched_skills"]

    import io
    import docx
    d = docx.Document()
    d.add_paragraph(cv)
    buf = io.BytesIO()
    d.save(buf)
    r = client.post("/api/match/file", data={"job_description": jd},
                    files={"file": ("cv.docx", buf.getvalue(),
                                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert r.status_code == 200 and "docker" in r.json()["matched_skills"]


def test_match_file_rejects_bad_input():
    jd = "x" * 60
    assert client.post("/api/match/file", data={"job_description": jd},
                       files={"file": ("cv.exe", b"MZ...", "application/octet-stream")}).status_code == 415
    assert client.post("/api/match/file", data={"job_description": jd},
                       files={"file": ("cv.txt", b"too short", "text/plain")}).status_code == 422


JD = ("We need a Python engineer with NLP and LLM experience. "
      "You will deploy services on AWS with Docker and Kubernetes.")
STRONG = ("Machine Learning Engineer. Python, NLP and LLM work. Deployed services on AWS "
          "with Docker and Kubernetes for three years.")
WEAK = ("Retail store supervisor. Managed rotas, stock counts and customer service for a "
        "busy high-street branch.")


def test_rank_orders_cvs_best_first():
    r = client.post("/api/match/rank", json={"job_description": JD, "resumes": [
        {"name": "weak", "text": WEAK}, {"name": "strong", "text": STRONG}]})
    assert r.status_code == 200, r.text
    ranking = r.json()["ranking"]
    assert [x["name"] for x in ranking] == ["strong", "weak"]
    assert ranking[0]["rank"] == 1 and ranking[0]["match_score"] >= ranking[1]["match_score"]


def test_rank_files_skips_unreadable():
    files = [("files", ("a.txt", STRONG.encode(), "text/plain")),
             ("files", ("b.txt", WEAK.encode(), "text/plain")),
             ("files", ("c.exe", b"MZ", "application/octet-stream"))]
    r = client.post("/api/match/rank/files", data={"job_description": JD}, files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 2 and body["ranking"][0]["name"] == "a.txt"
    assert body["skipped"][0]["name"] == "c.exe"


def test_rank_rejects_short_cv_and_too_many():
    assert client.post("/api/match/rank", json={"job_description": JD,
                       "resumes": [{"name": "x", "text": "short"}]}).status_code == 422
    many = [{"name": str(i), "text": STRONG} for i in range(11)]
    assert client.post("/api/match/rank", json={"job_description": JD, "resumes": many}).status_code == 422
