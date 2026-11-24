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
# Country names and major cities -> country code (also Adzuna's country codes).
COUNTRY_NAMES = {
    "uk": "gb", "united kingdom": "gb", "gb": "gb", "great britain": "gb", "england": "gb",
    "scotland": "gb", "wales": "gb", "northern ireland": "gb",
    "india": "in", "us": "us", "usa": "us", "united states": "us", "germany": "de", "france": "fr",
    "netherlands": "nl", "the netherlands": "nl", "holland": "nl", "canada": "ca", "australia": "au",
    "ireland": "ie", "spain": "es", "italy": "it", "poland": "pl", "singapore": "sg",
    "new zealand": "nz", "south africa": "za", "austria": "at", "belgium": "be", "switzerland": "ch",
    "brazil": "br", "mexico": "mx",
}
CITIES = {
    **dict.fromkeys(["london", "manchester", "birmingham", "edinburgh", "glasgow", "leeds", "bristol",
                     "cambridge", "oxford", "belfast", "cardiff", "liverpool", "newcastle", "sheffield",
                     "nottingham", "reading"], "gb"),
    **dict.fromkeys(["bangalore", "bengaluru", "mumbai", "delhi", "new delhi", "hyderabad", "chennai",
                     "pune", "kolkata", "gurgaon", "gurugram", "noida", "ahmedabad", "visakhapatnam",
                     "vizag", "kochi", "jaipur", "coimbatore"], "in"),
    **dict.fromkeys(["amsterdam", "rotterdam", "utrecht", "the hague", "den haag", "eindhoven",
                     "groningen", "delft", "leiden"], "nl"),
    **dict.fromkeys(["sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra"], "au"),
    **dict.fromkeys(["berlin", "munich", "münchen", "hamburg", "frankfurt", "cologne", "köln",
                     "stuttgart", "düsseldorf", "dusseldorf", "leipzig", "dresden", "nuremberg"], "de"),
    **dict.fromkeys(["paris", "lyon", "toulouse", "marseille", "nantes", "lille"], "fr"),
    **dict.fromkeys(["dublin", "cork", "galway", "limerick"], "ie"),
    **dict.fromkeys(["toronto", "vancouver", "montreal", "ottawa", "calgary", "waterloo"], "ca"),
    **dict.fromkeys(["new york", "san francisco", "seattle", "austin", "boston", "chicago",
                     "los angeles", "denver"], "us"),
}
ADZUNA_COUNTRIES = {**COUNTRY_NAMES, **CITIES}

# Countries offered in the UI: code -> (name, words that mark a remote job as open to it).
COUNTRIES = {
    "gb": ("United Kingdom", ["uk", "united kingdom", "europe", "emea"]),
    "in": ("India", ["india", "asia", "apac"]),
    "us": ("United States", ["usa", "us", "united states", "americas", "north america"]),
    "ca": ("Canada", ["canada", "americas", "north america"]),
    "ie": ("Ireland", ["ireland", "europe", "emea"]),
    "de": ("Germany", ["germany", "europe", "emea"]),
    "nl": ("Netherlands", ["netherlands", "europe", "emea"]),
    "fr": ("France", ["france", "europe", "emea"]),
    "au": ("Australia", ["australia", "apac"]),
    "sg": ("Singapore", ["singapore", "asia", "apac"]),
}
GLOBAL_WORDS = ("worldwide", "anywhere", "global")
INDEED_DOMAINS = {
    "us": ("Indeed", "www.indeed.com"), "nl": ("Indeed Netherlands", "nl.indeed.com"),
    "de": ("Indeed Germany", "de.indeed.com"), "fr": ("Indeed France", "fr.indeed.com"),
    "ie": ("Indeed Ireland", "ie.indeed.com"), "ca": ("Indeed Canada", "ca.indeed.com"),
    "sg": ("Indeed Singapore", "sg.indeed.com"),
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def job_site_links(keyword: str, location: str = "", country: Optional[str] = None) -> List[Dict]:
    """Search links on the job sites people actually use in that country.

    These sites have no public API, so HireSense links to their own search
    results for the same keyword and location instead of copying listings.
    """
    from urllib.parse import quote_plus
    kw, loc = (keyword or "").strip(), (location or "").strip()
    k, l, ks, ls = quote_plus(kw), quote_plus(loc), _slug(kw), _slug(loc)
    cc = (country or "").lower()
    place = loc or (COUNTRIES[cc][0] if cc in COUNTRIES else "")
    links = [{"name": "LinkedIn", "url": f"https://www.linkedin.com/jobs/search/?keywords={k}&location={quote_plus(place)}"}]
    if cc == "in":
        links += [
            {"name": "Naukri", "url": f"https://www.naukri.com/{ks}-jobs" + (f"-in-{ls}" if ls else "")},
            {"name": "Indeed India", "url": f"https://in.indeed.com/jobs?q={k}&l={l}"},
            {"name": "foundit", "url": f"https://www.foundit.in/srp/results?query={k}" + (f"&locations={l}" if loc else "")},
            {"name": "Internshala", "url": f"https://internshala.com/jobs/{ks}-jobs" + (f"-in-{ls}" if ls else "") + "/"},
            {"name": "Shine", "url": f"https://www.shine.com/job-search/{ks}-jobs" + (f"-in-{ls}" if ls else "")},
        ]
    elif cc == "gb":
        links += [
            {"name": "Indeed UK", "url": f"https://uk.indeed.com/jobs?q={k}&l={l}"},
            {"name": "Reed", "url": f"https://www.reed.co.uk/jobs/{ks}-jobs" + (f"-in-{ls}" if ls else "")},
            {"name": "Totaljobs", "url": f"https://www.totaljobs.com/jobs/{ks}" + (f"/in-{ls}" if ls else "")},
            {"name": "CV-Library", "url": f"https://www.cv-library.co.uk/{ks}-jobs" + (f"-in-{ls}" if ls else "")},
        ]
    elif cc == "au":
        links += [
            {"name": "Seek", "url": f"https://www.seek.com.au/{ks}-jobs" + (f"/in-{ls}" if ls else "")},
            {"name": "Indeed Australia", "url": f"https://au.indeed.com/jobs?q={k}&l={l}"},
        ]
    elif cc in INDEED_DOMAINS:
        name, domain = INDEED_DOMAINS[cc]
        links.append({"name": name, "url": f"https://{domain}/jobs?q={k}&l={l}"})
    else:
        links.append({"name": "Indeed", "url": f"https://www.indeed.com/jobs?q={k}&l={quote_plus(place)}"})
    return links


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


def classify(job: Dict, location: str = "", country: Optional[str] = None) -> Optional[str]:
    """How a job fits the (optional) country and city/region.

    Returns "local" (based there), "remote_country" (remote, open to that
    country or region), "remote_worldwide" (remote, open anywhere), "any"
    (no filter given) or None (does not fit).
    """
    loc = (location or "").strip().lower()
    remote_only = loc == "remote"
    if loc in {"any", "anywhere", "worldwide", "all", "remote"}:
        loc = ""
    cc = (country or "").lower() or ADZUNA_COUNTRIES.get(loc, "")
    if loc in COUNTRY_NAMES:          # the location just names a country
        loc = ""
    if remote_only and not job["remote"]:
        return None

    place = (job["location"] + " " + job.get("country", "")).lower()
    scope = job.get("remote_scope", "").lower()
    worldwide = job["remote"] and (not scope or any(w in scope for w in GLOBAL_WORDS))

    if not cc and not loc:
        return "any"
    if cc in COUNTRIES:
        name, words = COUNTRIES[cc]
        country_places = [k for k, v in ADZUNA_COUNTRIES.items() if v == cc and len(k) > 2]
        in_country = (job.get("country", "").lower() == cc or name.lower() in place
                      or any(re.search(rf"\b{re.escape(p)}\b", place) for p in country_places))
        if in_country and not job["remote"] and (not loc or loc in place):
            return "local"
        if job["remote"]:
            if in_country or any(w in scope for w in words):
                return "remote_country"
            if worldwide:
                return "remote_worldwide"
        return None
    # A city/region with no known country.
    if loc in place and not job["remote"]:
        return "local"
    if job["remote"] and loc in scope:
        return "remote_country"
    return "remote_worldwide" if worldwide else None


def _matches_location(job: Dict, location: str, country: Optional[str] = None) -> bool:
    return classify(job, location, country) is not None


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
    is_country = loc in COUNTRY_NAMES
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
                kept = []
                for j in found:
                    # Adzuna already filtered by country/location server-side.
                    fit = "local" if name == "adzuna" else classify(j, location, country)
                    if fit:
                        kept.append({**j, "fit": fit})
                found = kept
                jobs.extend(found)
                status[name] = {"ok": True, "count": len(found)}
            except Exception as e:  # one feed failing must not break the search
                status[name] = {"ok": False, "error": type(e).__name__}

    order = {"local": 0, "remote_country": 1, "any": 1, "remote_worldwide": 2}
    jobs.sort(key=lambda x: x.get("posted", ""), reverse=True)
    jobs.sort(key=lambda x: order.get(x.get("fit"), 3))   # stable: local first, newest first
    seen, unique = set(), []
    for j in jobs:
        k = (j["title"].lower(), j["company"].lower())
        if k not in seen:
            seen.add(k)
            unique.append(j)
    fits = {f: sum(j.get("fit") == f for j in unique) for f in ("local", "remote_country", "remote_worldwide")}
    return {"total": len(unique), "jobs": unique[:limit], "sources": status, "fit_counts": fits,
            "other_sites": job_site_links(keyword, location, country or ADZUNA_COUNTRIES.get((location or "").strip().lower()))}
