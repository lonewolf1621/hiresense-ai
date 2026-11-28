"""Owner/admin endpoints: token auth, stats, user suspension and deletion, settings, logs."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app import admin
from app.main import app

client = TestClient(app)
TOKEN = "test-admin-token-" + "x" * 24
H = {"X-Admin-Token": TOKEN}


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", TOKEN)
    admin._failures.clear()
    admin.settings.update(admin.DEFAULT_SETTINGS)
    yield
    admin.settings.update(admin.DEFAULT_SETTINGS)


def _user(password="correct-horse-1"):
    email = f"a{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": password, "name": "Admin Test"})
    assert r.status_code == 200, r.text
    return email, r.json()["access_token"]


def test_admin_disabled_without_token(monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN")
    assert client.get("/api/admin/stats", headers=H).status_code == 403
    monkeypatch.setenv("ADMIN_TOKEN", "too-short")
    assert client.get("/api/admin/stats", headers=H).status_code == 403


def test_wrong_token_rejected_and_rate_limited():
    assert client.get("/api/admin/stats").status_code == 401
    for _ in range(9):
        assert client.get("/api/admin/stats", headers={"X-Admin-Token": "wrong" * 6}).status_code == 401
    assert client.get("/api/admin/stats", headers=H).status_code == 429   # locked out even with the right token
    admin._failures.clear()
    assert client.get("/api/admin/stats", headers=H).status_code == 200


def test_stats_and_users():
    email, _ = _user()
    stats = client.get("/api/admin/stats", headers=H).json()
    assert stats["users"]["total"] >= 1 and "endpoints" in stats and stats["uptime_seconds"] >= 0
    users = client.get("/api/admin/users", headers=H).json()["users"]
    row = next(u for u in users if u["email"] == email)
    assert row["suspended"] is False and "password" not in row


def test_suspend_blocks_login_and_existing_tokens_then_unsuspend():
    email, token = _user()
    assert client.post(f"/api/admin/users/{email}/suspend", headers=H).status_code == 200
    assert client.post("/api/auth/login", json={"email": email, "password": "correct-horse-1"}).status_code == 403
    assert client.get("/api/profile", headers={"Authorization": f"Bearer {token}"}).status_code == 403
    assert client.post(f"/api/admin/users/{email}/unsuspend", headers=H).status_code == 200
    assert client.post("/api/auth/login", json={"email": email, "password": "correct-horse-1"}).status_code == 200


def test_delete_user():
    email, token = _user()
    assert client.delete(f"/api/admin/users/{email}", headers=H).status_code == 200
    assert client.get("/api/profile", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    assert client.delete(f"/api/admin/users/{email}", headers=H).status_code == 404


def test_settings_switch_features_off_and_show_banner():
    r = client.put("/api/admin/settings", headers=H,
                   json={"maintenance_banner": "Back at 6pm", "registration_enabled": False, "matching_enabled": False})
    assert r.status_code == 200 and r.json()["registration_enabled"] is False
    assert client.get("/api/status").json()["maintenance_banner"] == "Back at 6pm"
    reg = client.post("/api/auth/register", json={"email": "x@example.com", "password": "correct-horse-1", "name": "X"})
    assert reg.status_code == 503 and reg.json()["detail"] == "Back at 6pm"
    m = client.post("/api/match", json={"resume_text": "Python " * 20, "job_description": "Python " * 20})
    assert m.status_code == 503


def test_logs_record_events_without_passwords():
    email, _ = _user(password="very-secret-pass-9")
    client.post("/api/auth/login", json={"email": email, "password": "wrong-password-1"})
    items = client.get("/api/admin/logs?kind=events&limit=300", headers=H).json()["items"]
    types = {i["type"] for i in items if i.get("email") == email}
    assert {"user_registered", "login_failed"} <= types
    assert "very-secret-pass-9" not in str(items) and "wrong-password-1" not in str(items)
    reqs = client.get("/api/admin/logs?kind=requests", headers=H).json()["items"]
    assert any(r["route"] == "POST /api/auth/login" for r in reqs)


def test_clear_demo_data_requires_confirmation():
    _user()
    assert client.post("/api/admin/clear-demo-data", headers=H).status_code == 422
    r = client.post("/api/admin/clear-demo-data?confirm=DELETE", headers=H)
    assert r.status_code == 200 and r.json()["users_removed"] >= 1
    assert client.get("/api/admin/stats", headers=H).json()["users"]["total"] == 0
