"""Owner/admin tooling: token auth, request metrics, activity log and runtime settings.

Admin access is a single secret, ADMIN_TOKEN, set in the hosting dashboard
(never in the repo). Without it every admin endpoint answers 403. Wrong
tokens are rate-limited per client and logged.
"""
from __future__ import annotations

import hmac
import os
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import Header, HTTPException, Request

MIN_TOKEN_LENGTH = 24
STARTED = time.time()
_lock = threading.Lock()

# ---------------------------------------------------------------- settings
DEFAULT_SETTINGS = {
    "maintenance_banner": "",
    "registration_enabled": True,
    "matching_enabled": True,
    "job_search_enabled": True,
}
settings: Dict = dict(DEFAULT_SETTINGS)


def feature_on(name: str) -> None:
    """Raise 503 when the owner has switched a feature off."""
    if not settings.get(name, True):
        msg = settings.get("maintenance_banner") or "This feature is temporarily switched off."
        raise HTTPException(status_code=503, detail=msg)


# ---------------------------------------------------------------- metrics
_counts: Dict[str, int] = defaultdict(int)
_errors: Dict[str, int] = defaultdict(int)
_durations: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=500))
_requests: Deque[dict] = deque(maxlen=300)
_events: Deque[dict] = deque(maxlen=500)


def record_request(method: str, route: str, status: int, ms: float) -> None:
    if route.startswith("/api/admin") or route in ("/health", "/openapi.json", "/docs"):
        return
    key = f"{method} {route}"
    with _lock:
        _counts[key] += 1
        if status >= 500:
            _errors[key] += 1
        _durations[key].append(ms)
        _requests.append({"ts": time.time(), "route": key, "status": status, "ms": round(ms, 1)})


def log_event(type_: str, **detail) -> None:
    """Application events for the owner (sign-ups, logins, admin actions). No passwords or tokens."""
    with _lock:
        _events.append({"ts": time.time(), "type": type_, **detail})


def _pct(values, q):
    s = sorted(values)
    return round(s[min(len(s) - 1, int(q * len(s)))], 1) if s else None


def endpoint_stats() -> list:
    with _lock:
        rows = [{"endpoint": k, "requests": v, "errors_5xx": _errors.get(k, 0),
                 "p50_ms": _pct(_durations[k], 0.5), "p95_ms": _pct(_durations[k], 0.95)}
                for k, v in _counts.items()]
    return sorted(rows, key=lambda r: -r["requests"])


def recent(limit: int = 100, kind: str = "events") -> list:
    with _lock:
        items = list(_events if kind == "events" else _requests)[-limit:]
    return list(reversed(items))


def event_counts() -> Dict[str, int]:
    with _lock:
        out: Dict[str, int] = defaultdict(int)
        for e in _events:
            out[e["type"]] += 1
    return dict(out)


def reset_metrics() -> None:
    with _lock:
        _counts.clear(); _errors.clear(); _durations.clear(); _requests.clear()


# ---------------------------------------------------------------- auth
_failures: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=20))


def admin_enabled() -> bool:
    return len(os.getenv("ADMIN_TOKEN", "")) >= MIN_TOKEN_LENGTH


def require_admin(request: Request, x_admin_token: Optional[str] = Header(None)) -> None:
    client = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
              or (request.client.host if request.client else "unknown"))
    if not admin_enabled():
        raise HTTPException(status_code=403, detail="Admin is not configured (set ADMIN_TOKEN, 24+ characters)")
    now = time.time()
    recent_fails = [t for t in _failures[client] if now - t < 900]
    if len(recent_fails) >= 10:
        raise HTTPException(status_code=429, detail="Too many failed admin attempts; try again later")
    expected = os.getenv("ADMIN_TOKEN", "")
    if not x_admin_token or not hmac.compare_digest(x_admin_token.encode(), expected.encode()):
        _failures[client].append(now)
        log_event("admin_auth_failed", client=client)
        raise HTTPException(status_code=401, detail="Invalid admin token")


def uptime_seconds() -> int:
    return int(time.time() - STARTED)
