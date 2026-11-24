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

def api_call(method, endpoint, data=None):
    """Make API call"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        headers = get_headers()
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code == 200 or response.status_code == 201:
            return True, response.json()
        else:
            return False, response.json() if response.text else "Error occurred"
    except Exception as e:
        return False, str(e)

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
            phone = st.text_input("Phone", placeholder="+91 XXXXXXXXXX")
            reg_password = st.text_input("Password", type="password", placeholder="Create password", key="reg_password")
            
            if st.button("✍️ Register", use_container_width=True, key="register_btn"):
                if name and reg_email and reg_password:
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Resumes", "3", "+1 new")
    
    with col2:
        st.metric("💼 Applications", "12", "+2 this week")
    
    with col3:
        st.metric("⭐ Match Score", "78%", "+5%")
    
    with col4:
        st.metric("🎯 Target Jobs", "45", "Active")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Recent Applications")
        success, response = api_call("GET", "/applications", None)
        
        if success and response.get('applications'):
            apps_df = pd.DataFrame(response['applications'][:5])
            st.dataframe(apps_df[['jobTitle', 'company', 'status', 'matchScore']], use_container_width=True)
        else:
            st.info("No applications yet")
    
    with col2:
        st.subheader("📈 Quick Stats")
        st.write("""
        - **Profile Completion**: 85%
        - **Top Skills**: Python, SQL, React
        - **Experience**: 3+ Years
        - **Target Roles**: Senior Developer
        """)

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

def jobs_page():
    """Job search page"""
    st.title("💼 Find Jobs")
    st.info("Demo: shows sample listings. Live job feeds are not connected yet. "
            "Try the 🧠 Match CV page to score your CV against a real job description.")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        keyword = st.text_input("Job Title", placeholder="e.g., Python Developer")
    
    with col2:
        location = st.text_input("Location", value="India", placeholder="City/Region")
    
    with col3:
        source = st.selectbox("Source", ["All", "Indeed", "Naukri", "Internshala"])
    
    with col4:
        if st.button("🔍 Search", use_container_width=True):
            st.session_state.search_triggered = True
    
    st.markdown("---")
    
    if st.session_state.get('search_triggered'):
        if keyword:
            with st.spinner("Searching jobs..."):
                search_data = {
                    "keyword": keyword,
                    "location": location,
                    "source": None if source == "All" else source
                }
                
                success, response = api_call("POST", "/jobs/search", search_data)
                
                if success:
                    jobs = response.get('jobs', [])
                    st.success(f"Found {len(jobs)} jobs!")
                    
                    for idx, job in enumerate(jobs):
                        with st.expander(f"🏢 {job.get('title')} - {job.get('company')}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"**Company:** {job.get('company')}")
                                st.write(f"**Location:** {job.get('location')}")
                                st.write(f"**Salary:** {job.get('salary')}")
                                st.write(f"**Source:** {job.get('source')}")
                                st.write(f"**Description:** {job.get('description')[:200]}...")
                                
                                if job.get('skills'):
                                    st.write(f"**Skills:** {', '.join(job.get('skills'))}")
                            
                            with col2:
                                if st.button("✅ Apply", key=f"apply_{idx}"):
                                    app_data = {
                                        "jobId": str(idx),
                                        "jobTitle": job.get('title'),
                                        "company": job.get('company'),
                                        "matchScore": 85.0,
                                        "notes": ""
                                    }
                                    
                                    success, response = api_call("POST", "/applications", app_data)
                                    
                                    if success:
                                        st.success("✅ Applied successfully!")
                                    else:
                                        st.error(f"❌ Application failed: {response}")
                else:
                    st.error(f"❌ Search failed: {response}")
        else:
            st.warning("Please enter a job title")

def applications_page():
    """Applications tracking page"""
    st.title("📋 My Applications")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Applied", "Rejected", "Interview", "Offer"])
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Latest", "Match Score", "Company"])
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Get applications
    success, response = api_call("GET", "/applications", None)
    
    if success and response.get('applications'):
        apps = response['applications']
        
        # Filter
        if status_filter != "All":
            apps = [app for app in apps if app.get('status') == status_filter]
        
        # Display
        for app in apps:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**{app.get('jobTitle')}** - {app.get('company')}")
            
            with col2:
                status = app.get('status', 'Applied')
                status_color = {
                    'Applied': '🟡',
                    'Rejected': '🔴',
                    'Interview': '🟢',
                    'Offer': '✅'
                }
                st.write(f"{status_color.get(status, '⚪')} {status}")
            
            with col3:
                st.write(f"⭐ {app.get('matchScore', 0):.0f}%")
            
            with col4:
                st.write(f"📅 {app.get('appliedDate', 'N/A')}")
            
            st.divider()
    else:
        st.info("No applications yet")

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

    method = result.get("method")
    if method == "embeddings":
        st.caption(f"Method: embeddings ({result.get('model')}) + FAISS · weights {result.get('weights')}")
    elif method:
        st.caption("Method: lexical fallback (embedding model not loaded yet). Try again in a minute.")

# ============= MAIN APP =============
def main():
    """Main app logic"""
    
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
