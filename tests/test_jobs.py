"""Job search and application tracking (job feeds are mocked; no network)."""
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.services import job_feeds

client = TestClient(app)

JOB = {"id": "remotive-abc", "title": "Machine Learning Engineer", "company": "Acme",
       "location": "Remote (UK)", "remote_scope": "UK", "country": "", "remote": True,
       "description": "We need Python, PyTorch and MLOps experience.", "url": "https://example.com/job",
       "source": "Remotive", "posted": "2026-11-20", "salary": "", "tags": ["python"]}


def _token():
    email = f"j{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "correct-horse-1", "name": "J"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_html_to_text_keeps_structure():
    text = job_feeds.html_to_text("<p>About</p><ul><li>Python</li><li>SQL</li></ul>")
    assert "About" in text and "• Python" in text and "• SQL" in text and "<" not in text


def test_location_filter():
    onsite = {**JOB, "remote": False, "location": "London", "remote_scope": ""}
    assert job_feeds._matches_location(onsite, "london")
    assert not job_feeds._matches_location(onsite, "berlin")
    assert job_feeds._matches_location(JOB, "United Kingdom")          # remote, UK allowed
    assert job_feeds._matches_location(JOB, "")                       # anywhere
    assert not job_feeds._matches_location({**JOB, "remote_scope": "USA only", "location": "Remote (USA only)"}, "uk")


def test_search_survives_a_failing_feed(monkeypatch):
    monkeypatch.setattr(job_feeds, "fetch_remotive", lambda kw: [JOB])
    def boom(kw):
        raise TimeoutError()
    monkeypatch.setattr(job_feeds, "fetch_arbeitnow", boom)
    job_feeds._cache.clear()
    out = job_feeds.search("machine learning", "uk")
    assert out["total"] == 1 and out["sources"]["remotive"]["ok"]
    assert out["sources"]["arbeitnow"] == {"ok": False, "error": "TimeoutError"}


def test_search_endpoint_returns_full_description(monkeypatch):
    monkeypatch.setattr(job_feeds, "search", lambda *a, **k: {"total": 1, "jobs": [JOB], "sources": {}})
    h = _token()
    r = client.post("/api/jobs/search", json={"keyword": "ml", "location": "UK"}, headers=h)
    assert r.status_code == 200 and r.json()["jobs"][0]["description"].startswith("We need")
    assert client.get(f"/api/jobs/{JOB['id']}", headers=h).json()["company"] == "Acme"
    assert client.get("/api/jobs/missing", headers=h).status_code == 404
    assert client.post("/api/jobs/search", json={"keyword": "ml"}).status_code == 401


def test_applications_are_tracked_updated_and_deleted():
    h = _token()
    body = {"jobId": JOB["id"], "jobTitle": JOB["title"], "company": "Acme", "url": JOB["url"]}
    r = client.post("/api/applications", json=body, headers=h)
    assert r.status_code == 200
    aid = r.json()["application_id"]
    assert client.post("/api/applications", json=body, headers=h).json()["message"] == "Already tracked"

    apps = client.get("/api/applications", headers=h).json()["applications"]
    assert len(apps) == 1 and apps[0]["status"] == "Applied" and apps[0]["appliedDate"]

    assert client.put(f"/api/applications/{aid}?status=Interview", headers=h).status_code == 200
    assert client.get("/api/applications", headers=h).json()["applications"][0]["status"] == "Interview"
    assert client.put(f"/api/applications/{aid}?status=Bogus", headers=h).status_code == 422

    other = _token()
    assert client.get("/api/applications", headers=other).json()["applications"] == []

    assert client.delete(f"/api/applications/{aid}", headers=h).status_code == 200
    assert client.get("/api/applications", headers=h).json()["applications"] == []


def test_country_filter_india_and_uk():
    blr = {**JOB, "remote": False, "location": "Bangalore", "remote_scope": ""}
    london = {**JOB, "remote": False, "location": "London", "remote_scope": ""}
    india_remote = {**JOB, "location": "Remote (India)", "remote_scope": "India"}
    assert job_feeds._matches_location(blr, "", "in")
    assert not job_feeds._matches_location(london, "", "in")
    assert job_feeds._matches_location(london, "", "gb")
    assert job_feeds._matches_location(india_remote, "bangalore", "in")
    assert not job_feeds._matches_location(india_remote, "", "gb")


def test_job_site_links_per_country():
    india = {s["name"]: s["url"] for s in job_feeds.job_site_links("data scientist", "Pune", "in")}
    assert {"LinkedIn", "Naukri", "Indeed India", "foundit", "Internshala", "Shine"} <= set(india)
    assert india["Naukri"] == "https://www.naukri.com/data-scientist-jobs-in-pune"
    uk = {s["name"] for s in job_feeds.job_site_links("python", "", "gb")}
    assert {"LinkedIn", "Indeed UK", "Reed", "Totaljobs", "CV-Library"} <= uk
    assert {s["name"] for s in job_feeds.job_site_links("python")} == {"LinkedIn", "Indeed"}


def test_search_needs_only_a_keyword(monkeypatch):
    monkeypatch.setattr(job_feeds, "search", lambda *a, **k: {"total": 0, "jobs": [], "sources": {}})
    assert client.post("/api/jobs/search", json={"keyword": "python"}, headers=_token()).status_code == 200
