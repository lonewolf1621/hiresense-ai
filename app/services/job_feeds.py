"""Live job listings with full job descriptions, from public job-board APIs.

Sources (queried in parallel, results cached for 30 minutes):

* Remotive   – remote jobs worldwide, no key needed (https://remotive.com).
* Arbeitnow  – jobs across Europe, many remote, no key needed (https://www.arbeitnow.com).
* Adzuna     – UK, US, India and 16 more countries; used only when the
               ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables are set
               (free key from https://developer.adzuna.com). Adzuna returns a
               shortened description; the full advert is behind its link.

Each job is returned in one shape: id, title, company, location, country,
remote, description (plain text), url, source, posted, salary.
"""
from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

TIMEOUT = 15
CACHE_TTL = 30 * 60
HEADERS = {"User-Agent": "HireSense/1.0 (portfolio project; github.com/lonewolf1621/hiresense-ai)"}

# Adzuna country codes (https://developer.adzuna.com/overview).
ADZUNA_COUNTRIES = {
    "uk": "gb", "united kingdom": "gb", "gb": "gb", "england": "gb", "scotland": "gb", "wales": "gb",
    "london": "gb", "manchester": "gb", "birmingham": "gb", "edinburgh": "gb", "glasgow": "gb",
    "leeds": "gb", "bristol": "gb", "cambridge": "gb", "oxford": "gb",
    "us": "us", "usa": "us", "united states": "us", "india": "in", "germany": "de",
    "france": "fr", "netherlands": "nl", "canada": "ca", "australia": "au", "ireland": "ie",
    "spain": "es", "italy": "it", "poland": "pl", "singapore": "sg", "new zealand": "nz",
    "south africa": "za", "austria": "at", "belgium": "be", "switzerland": "ch", "brazil": "br",
    "mexico": "mx",
}

UK_CITIES = {"london", "manchester", "birmingham", "edinburgh", "glasgow", "leeds", "bristol",
             "cambridge", "oxford"}

_cache: Dict[tuple, tuple] = {}
_cache_lock = threading.Lock()


def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    for li in soup.find_all("li"):
        li.insert_before("\n• ")
    for tag in soup.find_all(["p", "br", "div", "h1", "h2", "h3", "h4", "ul", "ol"]):
        tag.insert_after("\n")
    text = soup.get_text()
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _job_id(source: str, key: str) -> str:
    return f"{source.lower()}-" + hashlib.sha1(key.encode()).hexdigest()[:12]


def _words(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z0-9+#.]+", (text or "").lower()) if w]


def _matches_keyword(job: Dict, keyword: str) -> bool:
    words = _words(keyword)
    if not words:
        return True
    title = job["title"].lower()
    haystack = title + " " + " ".join(job.get("tags", [])).lower()
    return all(w in haystack for w in words)


def _matches_location(job: Dict, location: str) -> bool:
    loc = (location or "").strip().lower()
    if not loc or loc in {"any", "anywhere", "worldwide", "all"}:
        return True
    if loc == "remote":
        return job["remote"]
    place = (job["location"] + " " + job.get("country", "")).lower()
    if loc in place:
        return True
    # Remote jobs open to this country/region (e.g. "UK", "Europe", "Worldwide").
    if job["remote"]:
        allowed = job.get("remote_scope", "").lower()
        aliases = {loc}
        if ADZUNA_COUNTRIES.get(loc) == "gb":
            aliases |= {"uk", "united kingdom", "europe", "emea"}
        return any(a in allowed for a in aliases) or any(
            w in allowed for w in ("worldwide", "anywhere", "global"))
    return False


def fetch_remotive(keyword: str) -> List[Dict]:
    r = requests.get("https://remotive.com/api/remote-jobs", params={"search": keyword, "limit": 100},
                     headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    jobs = []
    for j in r.json().get("jobs", []):
        scope = j.get("candidate_required_location") or "Worldwide"
        jobs.append({
            "id": _job_id("remotive", str(j.get("id") or j.get("url"))),
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "location": f"Remote ({scope})",
            "remote_scope": scope,
            "country": "",
            "remote": True,
            "description": html_to_text(j.get("description", "")),
            "url": j.get("url", ""),
            "source": "Remotive",
            "posted": (j.get("publication_date") or "")[:10],
            "salary": j.get("salary") or "",
            "tags": j.get("tags") or [],
        })
    return jobs


def fetch_arbeitnow(keyword: str, pages: int = 2) -> List[Dict]:
    jobs = []
    for page in range(1, pages + 1):
        r = requests.get("https://www.arbeitnow.com/api/job-board-api", params={"page": page},
                         headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        for j in r.json().get("data", []):
            created = j.get("created_at")
            jobs.append({
                "id": _job_id("arbeitnow", j.get("slug") or j.get("url", "")),
                "title": j.get("title", ""),
                "company": j.get("company_name", ""),
                "location": j.get("location", "") + (" · remote" if j.get("remote") else ""),
                "remote_scope": "Europe" if j.get("remote") else "",
                "country": "",
                "remote": bool(j.get("remote")),
                "description": html_to_text(j.get("description", "")),
                "url": j.get("url", ""),
                "source": "Arbeitnow",
                "posted": datetime.fromtimestamp(created, timezone.utc).strftime("%Y-%m-%d") if created else "",
                "salary": "",
                "tags": (j.get("tags") or []) + (j.get("job_types") or []),
            })
    return [j for j in jobs if _matches_keyword(j, keyword)]


def adzuna_enabled() -> bool:
    return bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"))


def fetch_adzuna(keyword: str, location: str, country: Optional[str]) -> List[Dict]:
    if not adzuna_enabled():
        return []
    loc = (location or "").strip().lower()
    cc = (country or ADZUNA_COUNTRIES.get(loc) or "gb").lower()
    # A country name picks the Adzuna country; a city or region is passed as "where".
    is_country = loc in ADZUNA_COUNTRIES and loc not in UK_CITIES
    where = "" if is_country or loc in {"", "remote", "any", "anywhere", "worldwide", "all"} else location
    params = {"app_id": os.getenv("ADZUNA_APP_ID"), "app_key": os.getenv("ADZUNA_APP_KEY"),
              "what": keyword, "results_per_page": 30, "content-type": "application/json"}
    if where:
        params["where"] = where
    r = requests.get(f"https://api.adzuna.com/v1/api/jobs/{cc}/search/1", params=params,
                     headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    jobs = []
    for j in r.json().get("results", []):
        lo, hi = j.get("salary_min"), j.get("salary_max")
        salary = f"{lo:,.0f}–{hi:,.0f}" if lo and hi and lo != hi else (f"{lo:,.0f}" if lo else "")
        jobs.append({
            "id": _job_id("adzuna", str(j.get("id"))),
            "title": j.get("title", ""),
            "company": (j.get("company") or {}).get("display_name", ""),
            "location": (j.get("location") or {}).get("display_name", ""),
            "remote_scope": "",
            "country": cc.upper(),
            "remote": "remote" in (j.get("title", "") + j.get("description", "")).lower(),
            "description": html_to_text(j.get("description", "")) + "\n\n(Shortened by Adzuna; full advert at the link.)",
            "url": j.get("redirect_url", ""),
            "source": "Adzuna",
            "posted": (j.get("created") or "")[:10],
            "salary": salary,
            "tags": [],
        })
    return jobs


def _cached(key: tuple, fn):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
    value = fn()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


def available_sources() -> List[str]:
    return ["Remotive", "Arbeitnow"] + (["Adzuna"] if adzuna_enabled() else [])


def search(keyword: str, location: str = "", source: Optional[str] = None,
           country: Optional[str] = None, limit: int = 50) -> Dict:
    """Search every enabled source; return jobs with full descriptions plus per-source status."""
    keyword = (keyword or "").strip()
    wanted = {s.lower() for s in available_sources()}
    if source and source.lower() != "all":
        wanted &= {source.lower()}

    tasks = {
        "remotive": lambda: _cached(("remotive", keyword.lower()), lambda: fetch_remotive(keyword)),
        "arbeitnow": lambda: _cached(("arbeitnow", keyword.lower()), lambda: fetch_arbeitnow(keyword)),
        "adzuna": lambda: _cached(("adzuna", keyword.lower(), (location or "").lower(), country),
                                  lambda: fetch_adzuna(keyword, location, country)),
    }
    status, jobs = {}, []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(fn) for name, fn in tasks.items() if name in wanted}
        for name, fut in futures.items():
            try:
                found = fut.result()
                if name != "adzuna":  # Adzuna already filtered by location server-side
                    found = [j for j in found if _matches_location(j, location)]
                jobs.extend(found)
                status[name] = {"ok": True, "count": len(found)}
            except Exception as e:  # one feed failing must not break the search
                status[name] = {"ok": False, "error": type(e).__name__}

    seen, unique = set(), []
    for j in sorted(jobs, key=lambda x: x.get("posted", ""), reverse=True):
        k = (j["title"].lower(), j["company"].lower())
        if k not in seen:
            seen.add(k)
            unique.append(j)
    return {"total": len(unique), "jobs": unique[:limit], "sources": status}
