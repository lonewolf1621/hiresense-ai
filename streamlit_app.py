import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
from streamlit_option_menu import option_menu
import time

# ============= CONFIG =============
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
st.set_page_config(page_title="HireSense AI", page_icon="🎯", layout="wide")

# ============= SESSION STATE =============
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# ============= HELPER FUNCTIONS =============
def get_headers():
    """Get request headers with auth token"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

API_TIMEOUT = 90  # the free Render API can take ~1 minute to wake from sleep


def wake_api():
    """Start waking the API in the background as soon as someone opens the app."""
    if st.session_state.get("api_wake_started"):
        return
    st.session_state.api_wake_started = True
    import threading
    root = API_BASE_URL[:-4] if API_BASE_URL.endswith("/api") else API_BASE_URL
    threading.Thread(target=lambda: requests.get(f"{root}/health", timeout=API_TIMEOUT),
                     daemon=True).start()


def api_call(method, endpoint, data=None):
    """Call the API; returns (ok, json_or_message)."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, json=data, headers=get_headers(), timeout=API_TIMEOUT)
    except requests.exceptions.Timeout:
        return False, "The server is still waking up (free hosting sleeps when idle). Please try again in a few seconds."
    except requests.exceptions.ConnectionError:
        return False, "Could not reach the server. Please try again in a minute."
    except Exception as e:
        return False, str(e)
    if response.status_code in (200, 201):
        return True, response.json()
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text or f"HTTP {response.status_code}"
    if isinstance(detail, list):  # FastAPI validation errors
        detail = "; ".join(f"{d.get('loc', [''])[-1]}: {d.get('msg')}" for d in detail)
    return False, detail

# ============= AUTH PAGES =============
def login_page():
    """Login page"""
    st.title("🎯 HireSense AI")
    st.markdown("### Smart Resume & Job Matching Platform")
    
    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("---")
            st.subheader("Login to Your Account")
            
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            if st.button("🔓 Login", use_container_width=True, key="login_btn"):
                if email and password:
                    with st.spinner("Logging in… (up to a minute if the server was asleep)"):
                        success, response = api_call("POST", "/auth/login", {
                            "email": email,
                            "password": password
                        })
                    
                    if success:
                        st.session_state.token = response.get('access_token')
                        st.session_state.user_id = response.get('user_id')
                        st.session_state.user_name = response.get('name')
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Login failed: {response}")
                else:
                    st.warning("Please enter email and password")
            
            st.markdown("---")
            st.markdown("### Don't have an account?")
            st.write("Create one below 👇")
        
        with col2:
            st.markdown("---")
            st.subheader("Create New Account")
            
            name = st.text_input("Full Name", placeholder="John Doe")
            reg_email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
            phone = st.text_input("Phone", placeholder="+44 7XXX XXXXXX")
            reg_password = st.text_input("Password", type="password", placeholder="At least 8 characters", key="reg_password")
            st.caption("Demo mode: accounts are kept in memory and reset when the free server restarts. "
                       "The CV matcher needs no account.")
            
            if st.button("✍️ Register", use_container_width=True, key="register_btn"):
                if name and reg_email and reg_password:
                    with st.spinner("Creating your account… (up to a minute if the server was asleep)"):
                        success, response = api_call("POST", "/auth/register", {
                            "name": name,
                            "email": reg_email,
                            "password": reg_password,
                            "phone": phone
                        })
                    
                    if success:
                        st.session_state.token = response.get('access_token')
                        st.session_state.user_id = response.get('user_id')
                        st.session_state.user_name = response.get('name')
                        st.success("✅ Account created successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Registration failed: {response}")
                else:
                    st.warning("Please fill in all fields")

# ============= DASHBOARD PAGES =============
def dashboard_page():
    """Main dashboard"""
    st.title(f"👋 Welcome, {st.session_state.user_name}!")
    ok, resp = api_call("GET", "/applications")
    apps = resp.get("applications", []) if ok else []
    scored = [a["matchScore"] for a in apps if a.get("matchScore") is not None]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Tracked jobs", len(apps))
    c2.metric("✅ Applied", sum(a.get("status") == "Applied" for a in apps))
    c3.metric("🗣️ Interviews", sum(a.get("status") == "Interview" for a in apps))
    c4.metric("⭐ Avg match", f"{sum(scored) / len(scored):.0f}%" if scored else "—")

    st.markdown("---")
    st.subheader("Recent applications")
    if apps:
        df = pd.DataFrame(apps[:8])
        cols = [c for c in ["jobTitle", "company", "status", "matchScore", "appliedDate"] if c in df]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("No applications yet. Start in 💼 Find Jobs.")
    st.caption("Demo mode: accounts and applications are kept in memory and reset when the free server restarts.")


def profile_page():
    """User profile page"""
    st.title("👤 My Profile")
    
    success, response = api_call("GET", "/profile", None)
    
    if success:
        profile = response.get('profile', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name", value=response.get('name', ''))
            email = st.text_input("Email", value=response.get('email', ''), disabled=True)
            phone = st.text_input("Phone", value=response.get('phone', ''))
        
        with col2:
            experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=profile.get('experience', 0))
            skills = st.multiselect(
                "Skills",
                ["Python", "Java", "JavaScript", "SQL", "AWS", "Docker", "React", "Node.js", "Machine Learning"],
                default=profile.get('skills', [])
            )
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            target_roles = st.multiselect(
                "Target Roles",
                ["Senior Developer", "Tech Lead", "Architect", "Manager", "Freelancer"],
                default=profile.get('targetRoles', [])
            )
        
        with col2:
            target_cities = st.multiselect(
                "Target Cities",
                ["Bangalore", "Hyderabad", "Pune", "Delhi", "Mumbai", "Remote"],
                default=profile.get('targetCities', [])
            )
        
        with col3:
            target_companies = st.multiselect(
                "Target Companies",
                ["Google", "Microsoft", "Amazon", "Meta", "Apple", "Tesla", "Startup"],
                default=profile.get('targetCompanies', [])
            )
        
        if st.button("💾 Save Profile", use_container_width=True):
            update_data = {
                "name": name,
                "phone": phone,
                "experience": experience,
                "skills": skills,
                "targetRoles": target_roles,
                "targetCities": target_cities,
                "targetCompanies": target_companies
            }
            
            success, response = api_call("PUT", "/profile", update_data)
            
            if success:
                st.success("✅ Profile updated successfully!")
            else:
                st.error(f"❌ Failed to update profile: {response}")
    else:
        st.error("Failed to load profile")

def resumes_page():
    """Resume management page"""
    st.title("📄 My Resumes")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("Upload New Resume")
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Upload section
    uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=['pdf', 'docx'])
    resume_name = st.text_input("Resume Name", placeholder="e.g., Senior_Developer_Resume")
    is_primary = st.checkbox("Set as Primary Resume")
    
    if st.button("📤 Upload Resume", use_container_width=True):
        if uploaded_file and resume_name:
            try:
                # Prepare multipart form data
                files = {'file': (uploaded_file.name, uploaded_file.getbuffer())}
                data = {'name': resume_name, 'isPrimary': is_primary}
                
                url = f"{API_BASE_URL}/resumes/upload"
                headers = get_headers()
                
                response = requests.post(url, files=files, data=data, headers=headers)
                
                if response.status_code == 200:
                    st.success("✅ Resume uploaded successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Upload failed: {response.json()}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("Please fill in all fields")
    
    st.markdown("---")
    
    # List resumes
    st.subheader("Your Resumes")
    success, response = api_call("GET", "/resumes", None)
    
    if success and response.get('resumes'):
        for resume in response['resumes']:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"📄 **{resume.get('name')}**")
                st.caption(f"Uploaded: {resume.get('uploadedDate', 'N/A')}")
            
            with col2:
                if st.button("👁️ View", key=f"view_{resume.get('name')}"):
                    st.info(f"URL: {resume.get('gcsUrl')}")
            
            with col3:
                if st.button("🗑️ Delete", key=f"del_{resume.get('name')}"):
                    st.warning("Delete functionality coming soon")
            
            st.divider()
    else:
        st.info("No resumes uploaded yet")

def track_job(job, status, score=None):
    ok, resp = api_call("POST", "/applications", {
        "jobId": job["id"], "jobTitle": job["title"], "company": job["company"],
        "matchScore": score, "url": job.get("url", ""), "location": job.get("location", ""),
        "source": job.get("source", ""), "status": status,
    })
    if ok:
        st.success("Added to My Applications" if resp.get("message") != "Already tracked"
                   else "Already in My Applications")
    else:
        st.error(f"Could not save: {resp}")


def jobs_page():
    """Live job search with full job descriptions."""
    st.title("💼 Find Jobs")
    st.caption("Live listings from Remotive (remote, worldwide) and Arbeitnow (Europe), plus Adzuna "
               "(UK, India, US and more) when its API key is configured, with quick links to LinkedIn, "
               "Naukri, Indeed, foundit, Internshala, Shine, Reed and others. Only the job title is required.")

    if "job_sources" not in st.session_state:
        ok, src = api_call("GET", "/jobs/sources")
        if ok:
            st.session_state.job_sources = src.get("sources", [])
            st.session_state.job_countries = src.get("countries", [])
    countries = st.session_state.get("job_countries", [])

    keyword = st.text_input("Job title or skill", placeholder="e.g. machine learning engineer", key="job_kw")
    c1, c2, c3 = st.columns(3)
    country_names = ["Any country"] + [c["name"] for c in countries]
    country_name = c1.selectbox("Country (optional)", country_names, key="job_country")
    location = c2.text_input("City / region (optional)", placeholder='e.g. Bangalore, London, or "Remote"',
                             key="job_loc")
    source = c3.selectbox("Source (optional)", ["All sources"] + st.session_state.get("job_sources", []),
                          key="job_src")
    country = next((c["code"] for c in countries if c["name"] == country_name), None)

    with st.expander("📄 Optional: add your CV to score each job against it"):
        cv_file = st.file_uploader("CV (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"], key="jobs_cv")
        if cv_file:
            st.session_state.jobs_cv_text = extract_file_text(cv_file)
        if st.session_state.get("jobs_cv_text"):
            st.caption(f"CV loaded ({len(st.session_state.jobs_cv_text)} characters).")

    if st.button("🔍 Search", type="primary", use_container_width=True, key="job_search_btn"):
        if len(keyword.strip()) < 2:
            st.warning("Enter a job title or skill")
            return
        with st.spinner("Searching live job boards…"):
            ok, resp = api_call("POST", "/jobs/search", {
                "keyword": keyword, "location": location.strip(), "country": country,
                "source": None if source == "All sources" else source})
        if not ok:
            st.error(f"Search failed: {resp}")
            return
        st.session_state.job_results = resp
        st.session_state.job_scores = {}

    result = st.session_state.get("job_results")
    if not result:
        return
    jobs = result.get("jobs", [])
    failed = [n for n, v in result.get("sources", {}).items() if not v.get("ok")]
    st.success(f"{len(jobs)} jobs found")
    if failed:
        st.caption("Unavailable right now: " + ", ".join(failed))
    other = result.get("other_sites", [])
    if other:
        st.markdown("**Search the same role on other job sites:**")
        for col, site in zip(st.columns(len(other)), other):
            col.link_button(site["name"], site["url"], use_container_width=True)
    if not jobs:
        st.info('No matches. Try a broader title, or set Location to "Remote" or leave it empty.')

    scores = st.session_state.setdefault("job_scores", {})
    cv_text = st.session_state.get("jobs_cv_text", "")
    for job in jobs:
        jid = job["id"]
        header = f"{job['title']} · {job['company']} · {job['location']}"
        if jid in scores:
            header = f"[{scores[jid]['match_score']:.0f}% match] " + header
        with st.expander(header):
            meta = [f"**Source:** {job['source']}"]
            if job.get("posted"):
                meta.append(f"**Posted:** {job['posted']}")
            if job.get("salary"):
                meta.append(f"**Salary:** {job['salary']}")
            st.markdown(" · ".join(meta))

            b1, b2, b3, b4 = st.columns(4)
            if job.get("url"):
                b1.link_button("🔗 Apply on site", job["url"], use_container_width=True)
            score = scores.get(jid, {}).get("match_score")
            if b2.button("✅ Mark as applied", key=f"applied_{jid}", use_container_width=True):
                track_job(job, "Applied", score)
            if b3.button("⭐ Save for later", key=f"save_{jid}", use_container_width=True):
                track_job(job, "Saved", score)
            if b4.button("🧠 Match my CV", key=f"match_{jid}", use_container_width=True,
                         disabled=not cv_text):
                with st.spinner("Matching…"):
                    ok, m = api_call("POST", "/match", {"resume_text": cv_text,
                                                        "job_description": job["description"][:30000]})
                if ok:
                    scores[jid] = m
                    st.rerun()
                else:
                    st.error(f"Matching failed: {m}")

            if jid in scores:
                m = scores[jid]
                st.markdown(f"**Match {m['match_score']:.0f}%** · matched: "
                            f"{', '.join(m['matched_skills']) or '—'} · missing: {', '.join(m['missing_skills']) or '—'}")

            st.text_area("Job description", job.get("description") or "No description provided.",
                         height=320, disabled=True, key=f"jd_{jid}")


def applications_page():
    """Applications you are tracking."""
    st.title("📋 My Applications")
    ok, resp = api_call("GET", "/applications")
    if not ok:
        st.error(f"Could not load applications: {resp}")
        return
    apps = resp.get("applications", [])
    statuses = resp.get("statuses", ["Saved", "Applied", "Interview", "Offer", "Rejected"])
    if not apps:
        st.info("Nothing tracked yet. In 💼 Find Jobs, open a job and click ✅ Mark as applied or ⭐ Save for later.")
        return

    counts = {s: sum(a.get("status") == s for a in apps) for s in statuses}
    for col, s in zip(st.columns(len(statuses)), statuses):
        col.metric(s, counts[s])
    status_filter = st.selectbox("Show", ["All"] + statuses, key="app_filter")
    st.markdown("---")

    for a in apps:
        if status_filter != "All" and a.get("status") != status_filter:
            continue
        c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
        title = f"**{a.get('jobTitle')}** · {a.get('company')}"
        if a.get("url"):
            title += f"  \n[open advert]({a['url']})"
        c1.markdown(title)
        c1.caption(" · ".join(x for x in [a.get("location"), a.get("source"), a.get("appliedDate")] if x))
        current = a.get("status", "Applied")
        new = c2.selectbox("Status", statuses, index=statuses.index(current) if current in statuses else 1,
                           key=f"status_{a['id']}", label_visibility="collapsed")
        if new != current:
            ok, r = api_call("PUT", f"/applications/{a['id']}?status={new}")
            if ok:
                st.rerun()
            st.error(f"Update failed: {r}")
        c3.write(f"⭐ {a['matchScore']:.0f}%" if a.get("matchScore") is not None else "—")
        if c4.button("🗑️", key=f"del_app_{a['id']}", help="Remove"):
            ok, r = api_call("DELETE", f"/applications/{a['id']}")
            if ok:
                st.rerun()
            st.error(f"Delete failed: {r}")
        st.divider()

# ============= CV <-> JOB MATCHER =============
def extract_file_text(uploaded):
    """Read text from an uploaded PDF, DOCX or TXT file."""
    name = uploaded.name.lower()
    try:
        if name.endswith(".pdf"):
            import pdfplumber
            with pdfplumber.open(uploaded) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        if name.endswith(".docx"):
            import docx
            return "\n".join(p.text for p in docx.Document(uploaded).paragraphs)
        return uploaded.read().decode("utf-8", errors="ignore")
    except Exception as e:
        st.error(f"Could not read {uploaded.name}: {e}")
        return ""


def match_page():
    """Score a CV against a job description with the /api/match endpoint."""
    st.title("🧠 CV ↔ Job Matcher")
    st.caption(
        "Skill extraction + 384-dim MiniLM sentence embeddings + FAISS retrieval. "
        "For each job requirement, the matcher finds the CV line that supports it best."
    )

    mode = st.radio("Mode", ["One CV, detailed report", "Rank several CVs for one job"],
                    horizontal=True, key="match_mode")
    if mode.startswith("Rank"):
        rank_section()
        return

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your CV")
        cv_file = st.file_uploader("Upload CV (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"], key="match_cv_file")
        cv_default = extract_file_text(cv_file) if cv_file else ""
        cv_text = st.text_area("…or paste it", value=cv_default, height=300, key=f"match_cv_text_{cv_file.name if cv_file else 'none'}")
    with col2:
        st.subheader("Job description")
        jd_text = st.text_area("Paste the job description", height=380, key="match_jd_text")

    if st.button("🔍 Match", type="primary", use_container_width=True, key="match_btn"):
        if len(cv_text.strip()) < 50 or len(jd_text.strip()) < 50:
            st.warning("Please provide at least 50 characters for both the CV and the job description.")
            return
        with st.spinner("Matching… (the free server can take up to a minute to wake up)"):
            try:
                resp = requests.post(
                    f"{API_BASE_URL}/match",
                    json={"resume_text": cv_text, "job_description": jd_text},
                    timeout=120,
                )
            except Exception as e:
                st.error(f"Could not reach the matching service: {e}")
                return
        if resp.status_code != 200:
            st.error(f"Matching failed ({resp.status_code}): {resp.text[:300]}")
            return
        st.session_state.match_result = resp.json()

    result = st.session_state.get("match_result")
    if not result:
        return

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Overall match", f"{result['match_score']:.0f}%")
    m2.metric("Skill coverage", "n/a" if result.get("skill_score") is None else f"{result['skill_score']:.0f}%")
    m3.metric("Semantic coverage", f"{result['semantic_score']:.0f}%")
    st.progress(min(1.0, max(0.0, result["match_score"] / 100)))

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("**✅ Matched skills**")
        st.write(", ".join(result["matched_skills"]) or "—")
    with s2:
        st.markdown("**❌ Missing skills**")
        st.write(", ".join(result["missing_skills"]) or "—")
    with s3:
        st.markdown("**➕ Extra skills in your CV**")
        st.write(", ".join(result["extra_skills"]) or "—")

    st.subheader("Evidence: requirement → best supporting CV line")
    for ev in result.get("evidence", []):
        with st.container():
            st.markdown(f"**Requirement:** {ev['requirement']}")
            if ev.get("cv_evidence"):
                st.markdown(f"> {ev['cv_evidence']}")
            else:
                st.markdown("> _No supporting line found in your CV_")
            st.caption(f"similarity {ev['similarity']:.2f}")

    st.subheader("Suggestions")
    for tip in result.get("suggestions", []):
        st.write(f"• {tip}")

    st.download_button("⬇️ Download report (Markdown)", data=match_report(result),
                       file_name="hiresense_match_report.md", mime="text/markdown",
                       key="match_report_dl")

    method = result.get("method")
    if method == "embeddings":
        st.caption(f"Method: embeddings ({result.get('model')}) + FAISS · weights {result.get('weights')}")
    elif method:
        st.caption("Method: lexical fallback (embedding model not loaded yet). Try again in a minute.")

def match_report(result):
    """A Markdown summary of one match result, for download."""
    lines = [
        "# HireSense match report", "",
        f"- Overall match: {result['match_score']:.0f}%",
        "- Skill coverage: " + ("n/a" if result.get("skill_score") is None else f"{result['skill_score']:.0f}%"),
        f"- Semantic coverage: {result['semantic_score']:.0f}%", "",
        "## Skills",
        f"- Matched: {', '.join(result['matched_skills']) or '—'}",
        f"- Missing: {', '.join(result['missing_skills']) or '—'}",
        f"- Extra in CV: {', '.join(result['extra_skills']) or '—'}", "",
        "## Evidence (requirement → best CV line)",
    ]
    for ev in result.get("evidence", []):
        lines.append(f"- **{ev['requirement']}**")
        lines.append(f"  - {ev.get('cv_evidence') or 'No supporting line found'} (similarity {ev['similarity']:.2f})")
    lines += ["", "## Suggestions"] + [f"- {t}" for t in result.get("suggestions", [])]
    lines += ["", f"_Method: {result.get('method')} · model {result.get('model')}_"]
    return "\n".join(lines)


def rank_section():
    """Rank up to 10 CVs against one job with /api/match/rank/files."""
    files = st.file_uploader("Upload 2–10 CVs (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"],
                             accept_multiple_files=True, key="rank_files")
    jd_text = st.text_area("Job description", height=250, key="rank_jd_text")
    if st.button("🏆 Rank CVs", type="primary", use_container_width=True, key="rank_btn"):
        if not files or len(files) > 10:
            st.warning("Upload between 1 and 10 CVs.")
            return
        if len(jd_text.strip()) < 50:
            st.warning("The job description needs at least 50 characters.")
            return
        payload = [("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in files]
        with st.spinner("Ranking… (the free server can take up to a minute to wake up)"):
            try:
                resp = requests.post(f"{API_BASE_URL}/match/rank/files", data={"job_description": jd_text},
                                     files=payload, timeout=300)
            except Exception as e:
                st.error(f"Could not reach the matching service: {e}")
                return
        if resp.status_code != 200:
            st.error(f"Ranking failed ({resp.status_code}): {resp.text[:300]}")
            return
        st.session_state.rank_result = resp.json()

    result = st.session_state.get("rank_result")
    if not result:
        return
    import pandas as pd
    table = pd.DataFrame([{
        "Rank": r["rank"], "CV": r["name"], "Match %": round(r["match_score"]),
        "Skills %": None if r["skill_score"] is None else round(r["skill_score"]),
        "Semantic %": round(r["semantic_score"]),
        "Missing skills": ", ".join(r["missing_skills"][:6]),
    } for r in result["ranking"]])
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.download_button("⬇️ Download ranking (CSV)", data=table.to_csv(index=False),
                       file_name="hiresense_ranking.csv", mime="text/csv", key="rank_dl")
    for r in result["ranking"]:
        with st.expander(f"#{r['rank']} {r['name']} — {r['match_score']:.0f}%"):
            st.write("**Matched:** " + (", ".join(r["matched_skills"]) or "—"))
            st.write("**Missing:** " + (", ".join(r["missing_skills"]) or "—"))
            for ev in r.get("top_evidence", []):
                st.markdown(f"- {ev['requirement']}  \n  > {ev.get('cv_evidence') or '_no supporting line_'}")
    for s in result.get("skipped", []):
        st.caption(f"Skipped {s['name']}: {s['reason']}")


# ============= MAIN APP =============
def main():
    """Main app logic"""
    wake_api()

    if not st.session_state.token:
        login_tab, match_tab = st.tabs(["🔐 Login / Register", "🧠 Try the CV ↔ Job Matcher"])
        with login_tab:
            login_page()
        with match_tab:
            match_page()
    else:
        # Sidebar
        with st.sidebar:
            st.title("🎯 HireSense AI")
            st.write(f"Welcome, **{st.session_state.user_name}**")
            
            selected = option_menu(
                menu_title="Menu",
                options=["Dashboard", "Match CV", "Profile", "Resumes", "Find Jobs", "Applications", "Logout"],
                icons=["speedometer2", "bullseye", "person", "file-earmark", "briefcase", "clipboard", "box-arrow-right"],
                menu_icon="cast",
                default_index=0,
            )
            
            st.markdown("---")
            
            if selected == "Logout":
                st.session_state.token = None
                st.session_state.user_id = None
                st.session_state.user_name = None
                st.success("Logged out successfully!")
                time.sleep(1)
                st.rerun()
        
        # Main content
        if selected == "Dashboard":
            dashboard_page()
        elif selected == "Match CV":
            match_page()
        elif selected == "Profile":
            profile_page()
        elif selected == "Resumes":
            resumes_page()
        elif selected == "Find Jobs":
            jobs_page()
        elif selected == "Applications":
            applications_page()

if __name__ == "__main__":
    main()
