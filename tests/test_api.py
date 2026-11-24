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
