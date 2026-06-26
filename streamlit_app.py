import streamlit as st
import requests
import re

st.set_page_config(
    page_title="HireSense AI - Universal Career Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CONFIG
# =========================================================

API_URL = "https://hiresense-ai-3k4d.onrender.com/analyze"

# =========================================================
# STYLING
# =========================================================

st.markdown("""
<style>
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px 30px;
        border: none;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    h1 {
        color: #667eea;
        text-align: center;
    }

    h2 {
        color: #764ba2;
        border-bottom: 2px solid #667eea;
        padding-bottom: 10px;
    }

    h3 {
        color: #667eea;
    }

    [data-testid="metric-container"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
    }

    .score-box {
        color: white;
        padding: 28px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# FIELD DATA
# =========================================================

fields_data = {
    "💻 Information Technology": {
        "id": "IT",
        "roles": [
            "Backend Developer",
            "Frontend Developer",
            "Full Stack Developer",
            "DevOps Engineer",
            "Data Engineer",
            "ML Engineer",
            "Cloud Architect",
            "QA Engineer"
        ],
        "skills": ["Python", "Java", "AWS", "Docker", "React", "SQL", "Kubernetes", "Git", "REST API"],
        "keywords": ["Development", "Software", "Engineering", "Cloud", "Database", "Architecture"],
        "salary": {
            "Entry": "₹6-18 LPA",
            "Mid": "₹18-50 LPA",
            "Senior": "₹50-100 LPA",
            "Lead": "₹100-200+ LPA"
        },
        "cities": {
            "Bangalore": 1.40,
            "Mumbai": 1.35,
            "Delhi NCR": 1.25,
            "Hyderabad": 1.20,
            "Pune": 1.15,
            "Chennai": 1.10
        },
        "path": "Junior Developer → Developer → Senior Developer → Tech Lead → Architect → CTO"
    },

    "💰 Finance & Banking": {
        "id": "Finance",
        "roles": [
            "Investment Banker",
            "Financial Analyst",
            "Risk Manager",
            "Portfolio Manager",
            "Compliance Officer",
            "Credit Analyst",
            "Trading Analyst"
        ],
        "skills": ["Excel", "Financial Modeling", "Risk Analysis", "Bloomberg", "SQL", "Valuation"],
        "keywords": ["Analysis", "Investment", "Banking", "Risk", "Portfolio", "Trading"],
        "salary": {
            "Entry": "₹8-22 LPA",
            "Mid": "₹25-75 LPA",
            "Senior": "₹75-150 LPA",
            "Lead": "₹150-300+ LPA"
        },
        "cities": {
            "Mumbai": 1.40,
            "Delhi NCR": 1.35,
            "Bangalore": 1.30,
            "Pune": 1.20,
            "Chennai": 1.15
        },
        "path": "Analyst → Senior Analyst → Associate → Manager → VP → Director → MD"
    },

    "📊 Marketing & Advertising": {
        "id": "Marketing",
        "roles": [
            "Digital Marketing Manager",
            "Content Strategist",
            "Brand Manager",
            "SEO Specialist",
            "Growth Marketer",
            "Product Marketing Manager",
            "Marketing Analyst"
        ],
        "skills": ["Google Analytics", "SEO", "Content Strategy", "Salesforce", "Social Media", "Copywriting"],
        "keywords": ["Campaign", "Strategy", "Marketing", "Digital", "Analytics", "Brand", "Growth"],
        "salary": {
            "Entry": "₹6-15 LPA",
            "Mid": "₹15-45 LPA",
            "Senior": "₹45-90 LPA",
            "Lead": "₹90-180+ LPA"
        },
        "cities": {
            "Mumbai": 1.35,
            "Delhi NCR": 1.30,
            "Bangalore": 1.25,
            "Pune": 1.15,
            "Hyderabad": 1.10
        },
        "path": "Marketing Associate → Marketing Manager → Senior Manager → Director → VP Marketing → CMO"
    },

    "🎨 Design & UX": {
        "id": "Design",
        "roles": [
            "Product Designer",
            "UX Designer",
            "UI Designer",
            "Interaction Designer",
            "Design Lead",
            "UX Researcher",
            "Visual Designer"
        ],
        "skills": ["Figma", "Adobe XD", "Prototyping", "User Research", "Wireframing", "Design Systems"],
        "keywords": ["Design", "User Experience", "Interface", "Prototype", "Visual", "Research"],
        "salary": {
            "Entry": "₹7-18 LPA",
            "Mid": "₹18-50 LPA",
            "Senior": "₹50-100 LPA",
            "Lead": "₹100-180+ LPA"
        },
        "cities": {
            "Bangalore": 1.35,
            "Mumbai": 1.30,
            "Delhi NCR": 1.25,
            "Pune": 1.20,
            "Hyderabad": 1.15
        },
        "path": "Junior Designer → Designer → Senior Designer → Design Lead → Head of Design → CDO"
    },

    "👥 Human Resources": {
        "id": "HR",
        "roles": [
            "Recruiter",
            "HR Manager",
            "Talent Acquisition Specialist",
            "HR Business Partner",
            "Learning & Development Manager",
            "Compensation Specialist",
            "Employee Relations Manager"
        ],
        "skills": ["HRIS", "Recruitment", "ATS", "Employee Relations", "Payroll", "Talent Management"],
        "keywords": ["Recruitment", "HR", "Talent", "Employee", "Hiring", "Culture", "Engagement"],
        "salary": {
            "Entry": "₹6-14 LPA",
            "Mid": "₹14-40 LPA",
            "Senior": "₹40-80 LPA",
            "Lead": "₹80-150+ LPA"
        },
        "cities": {
            "Mumbai": 1.30,
            "Bangalore": 1.25,
            "Delhi NCR": 1.25,
            "Pune": 1.15,
            "Hyderabad": 1.10
        },
        "path": "HR Associate → HR Manager → Senior HR Manager → HR Director → VP HR → CHRO"
    },

    "📈 Sales & Business Development": {
        "id": "Sales",
        "roles": [
            "Sales Executive",
            "Account Manager",
            "Sales Manager",
            "Business Development Manager",
            "Inside Sales Specialist",
            "Regional Sales Manager",
            "Enterprise Sales Manager"
        ],
        "skills": ["Salesforce", "CRM", "Negotiation", "Pipeline Management", "Forecasting", "Lead Generation"],
        "keywords": ["Sales", "Revenue", "Account", "Customer", "Pipeline", "Growth", "Targets"],
        "salary": {
            "Entry": "₹6-20 LPA",
            "Mid": "₹20-60 LPA",
            "Senior": "₹60-120 LPA",
            "Lead": "₹120-250+ LPA"
        },
        "cities": {
            "Mumbai": 1.40,
            "Delhi NCR": 1.35,
            "Bangalore": 1.25,
            "Pune": 1.20,
            "Hyderabad": 1.15
        },
        "path": "Sales Executive → Senior Executive → Sales Manager → Regional Manager → Sales Director → CRO"
    },

    "📋 Consulting": {
        "id": "Consulting",
        "roles": [
            "Management Consultant",
            "Business Analyst",
            "Strategy Consultant",
            "Operations Consultant",
            "Implementation Consultant",
            "Senior Consultant"
        ],
        "skills": ["Problem Solving", "PowerPoint", "Excel", "Data Analysis", "Project Management", "Strategic Thinking"],
        "keywords": ["Consulting", "Strategy", "Analysis", "Implementation", "Operations", "Transformation"],
        "salary": {
            "Entry": "₹12-30 LPA",
            "Mid": "₹30-80 LPA",
            "Senior": "₹80-180 LPA",
            "Lead": "₹180-350+ LPA"
        },
        "cities": {
            "Delhi NCR": 1.35,
            "Mumbai": 1.30,
            "Bangalore": 1.25,
            "Hyderabad": 1.15,
            "Pune": 1.10
        },
        "path": "Analyst → Consultant → Senior Consultant → Manager → Principal → Partner"
    },

    "⚕️ Healthcare": {
        "id": "Healthcare",
        "roles": [
            "Doctor",
            "Nurse",
            "Healthcare Administrator",
            "Medical Technologist",
            "Pharmacist",
            "Clinical Manager",
            "Hospital Manager"
        ],
        "skills": ["Patient Care", "Medical Knowledge", "EHR", "Clinical Skills", "Healthcare IT", "Compliance"],
        "keywords": ["Healthcare", "Medical", "Patient", "Clinical", "Hospital", "Treatment"],
        "salary": {
            "Entry": "₹6-20 LPA",
            "Mid": "₹20-50 LPA",
            "Senior": "₹50-120 LPA",
            "Lead": "₹120-250+ LPA"
        },
        "cities": {
            "Mumbai": 1.30,
            "Delhi NCR": 1.25,
            "Bangalore": 1.20,
            "Chennai": 1.20,
            "Pune": 1.15
        },
        "path": "Resident → Specialist → Senior Specialist → HOD → Medical Director → CMO"
    },

    "🔗 Supply Chain & Logistics": {
        "id": "SupplyChain",
        "roles": [
            "Supply Chain Manager",
            "Logistics Manager",
            "Procurement Manager",
            "Operations Manager",
            "Demand Planner",
            "Warehouse Manager",
            "Inventory Analyst"
        ],
        "skills": ["SAP", "Logistics", "Procurement", "Inventory Management", "Demand Planning", "Vendor Management"],
        "keywords": ["Supply Chain", "Logistics", "Inventory", "Procurement", "Operations", "Warehouse"],
        "salary": {
            "Entry": "₹5-15 LPA",
            "Mid": "₹15-45 LPA",
            "Senior": "₹45-90 LPA",
            "Lead": "₹90-180+ LPA"
        },
        "cities": {
            "Mumbai": 1.35,
            "Bangalore": 1.25,
            "Delhi NCR": 1.25,
            "Chennai": 1.20,
            "Pune": 1.15,
            "Ahmedabad": 1.10
        },
        "path": "Executive → Senior Executive → Manager → Senior Manager → Director → VP Supply Chain → CSCO"
    },

    "🌱 Renewable Energy & Sustainability": {
        "id": "RenewableEnergy",
        "roles": [
            "Solar Engineer",
            "Wind Energy Specialist",
            "Sustainability Manager",
            "Environmental Engineer",
            "Energy Analyst",
            "Project Manager",
            "ESG Analyst"
        ],
        "skills": ["Solar Technology", "Wind Energy", "Environmental Science", "GIS", "Energy Modeling", "Sustainability Reporting"],
        "keywords": ["Renewable Energy", "Sustainability", "Solar", "Wind", "Green Technology", "ESG", "Climate"],
        "salary": {
            "Entry": "₹6-18 LPA",
            "Mid": "₹18-50 LPA",
            "Senior": "₹50-100 LPA",
            "Lead": "₹100-200+ LPA"
        },
        "cities": {
            "Bangalore": 1.30,
            "Hyderabad": 1.25,
            "Gujarat": 1.25,
            "Maharashtra": 1.20,
            "Delhi NCR": 1.15,
            "Chennai": 1.10
        },
        "path": "Junior Engineer → Engineer → Senior Engineer → Project Manager → Energy Manager → Director"
    },

    "⚖️ Law & Legal Services": {
        "id": "Law",
        "roles": [
            "Associate Lawyer",
            "Legal Counsel",
            "Paralegal",
            "Legal Manager",
            "In-house Counsel",
            "Senior Attorney",
            "Compliance Lawyer"
        ],
        "skills": ["Legal Research", "Contract Law", "Corporate Law", "Legal Writing", "Litigation", "Compliance"],
        "keywords": ["Law", "Legal", "Compliance", "Contract", "Attorney", "Litigation", "Regulation"],
        "salary": {
            "Entry": "₹6-18 LPA",
            "Mid": "₹18-60 LPA",
            "Senior": "₹60-150 LPA",
            "Lead": "₹150-300+ LPA"
        },
        "cities": {
            "Mumbai": 1.35,
            "Delhi NCR": 1.35,
            "Bangalore": 1.25,
            "Chennai": 1.20,
            "Pune": 1.15
        },
        "path": "Associate → Senior Associate → Counsel → Senior Counsel → Partner / General Counsel"
    }
}

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def extract_text_from_file(uploaded_file):
    """
    Extract text from TXT, PDF, DOCX files.
    TXT works by default.
    PDF/DOCX work if optional packages are installed.
    """
    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    try:
        if file_name.endswith(".txt"):
            return uploaded_file.getvalue().decode("utf-8", errors="ignore")

        elif file_name.endswith(".pdf"):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
            except Exception:
                st.warning("PDF extraction needs PyPDF2. If this fails, paste text manually.")
                return ""

        elif file_name.endswith(".docx") or file_name.endswith(".doc"):
            try:
                from docx import Document
                doc = Document(uploaded_file)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text
            except Exception:
                st.warning("DOCX extraction needs python-docx. If this fails, paste text manually.")
                return ""

        else:
            return ""

    except Exception as e:
        st.error(f"File extraction error: {e}")
        return ""


def score_resume_universal(resume_text, field_data):
    resume_lower = resume_text.lower()
    word_count = len(resume_text.split())

    score = 0
    strengths = []
    issues = []
    improvements = []

    # Length
    if 300 <= word_count <= 800:
        score += 15
        strengths.append("Resume length is within the recommended 300-800 word range.")
    elif word_count < 300:
        score += 6
        issues.append("Resume looks too short.")
        improvements.append("Add more achievements, project details, responsibilities, and measurable outcomes.")
    else:
        score += 8
        issues.append("Resume may be too long.")
        improvements.append("Trim older or less relevant details. Keep the strongest achievements.")

    # Contact info
    has_email = bool(re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text))
    has_phone = bool(re.search(r"\+?\d[\d\s-]{8,}", resume_text))

    if has_email:
        score += 5
        strengths.append("Email address found.")
    else:
        issues.append("Email address not detected.")
        improvements.append("Add your professional email at the top.")

    if has_phone:
        score += 5
        strengths.append("Phone number found.")
    else:
        issues.append("Phone number not detected.")
        improvements.append("Add your phone number at the top.")

    # Skills
    skills = field_data.get("skills", [])
    matched_skills = [skill for skill in skills if skill.lower() in resume_lower]
    missing_skills = [skill for skill in skills if skill.lower() not in resume_lower]

    if skills:
        skill_score = (len(matched_skills) / len(skills)) * 30
        score += skill_score

    if matched_skills:
        strengths.append(f"Found relevant skills: {', '.join(matched_skills)}")
    else:
        issues.append("No strong field-specific skills detected.")
        improvements.append(f"Add relevant skills such as: {', '.join(skills[:5])}")

    if missing_skills:
        improvements.append(f"Consider adding these field-relevant skills if applicable: {', '.join(missing_skills[:5])}")

    # Keywords
    keywords = field_data.get("keywords", [])
    matched_keywords = [kw for kw in keywords if kw.lower() in resume_lower]

    if keywords:
        keyword_score = (len(matched_keywords) / len(keywords)) * 15
        score += keyword_score

    if matched_keywords:
        strengths.append(f"Industry keywords found: {', '.join(matched_keywords)}")
    else:
        improvements.append(f"Add industry keywords naturally: {', '.join(keywords[:5])}")

    # Action verbs
    action_verbs = [
        "led", "managed", "built", "created", "developed", "designed",
        "implemented", "improved", "increased", "reduced", "optimized",
        "launched", "delivered", "analyzed", "coordinated", "negotiated",
        "advised", "consulted", "executed", "planned"
    ]
    action_count = sum(1 for verb in action_verbs if verb in resume_lower)

    if action_count >= 6:
        score += 15
        strengths.append("Strong use of action verbs.")
    elif action_count >= 2:
        score += 8
        improvements.append("Use more powerful action verbs like Led, Built, Improved, Delivered, Negotiated.")
    else:
        issues.append("Resume language may be passive.")
        improvements.append("Start bullet points with strong action verbs.")

    # Metrics
    metrics = re.findall(r"\d+[%+x]?", resume_text)

    if len(metrics) >= 5:
        score += 15
        strengths.append("Good use of measurable numbers and achievements.")
    elif len(metrics) >= 1:
        score += 8
        improvements.append("Add more numbers, percentages, revenue, savings, timelines, or impact metrics.")
    else:
        issues.append("Few or no measurable achievements found.")
        improvements.append("Add measurable impact, for example: Increased efficiency by 30%, Managed ₹10L budget, Reduced cost by 20%.")

    final_score = min(round(score, 1), 100)

    return {
        "score": final_score,
        "ats_score": final_score,
        "word_count": word_count,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_keywords": matched_keywords,
        "strengths": strengths,
        "issues": issues,
        "improvements": improvements,
        "action_count": action_count,
        "metric_count": len(metrics)
    }


def call_match_api(resume, jd):
    response = requests.post(
        API_URL,
        json={"resume": resume, "job_description": jd},
        timeout=30
    )

    if response.status_code == 200:
        return response.json()

    raise Exception(f"API returned status {response.status_code}")


def render_match_results(data):
    score = data.get("match_score_percent", 0)
    matched = data.get("matched_skills", [])
    missing = data.get("missing_skills", [])
    suggestions = data.get("suggestions", [])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Match Score", f"{score}%")

    with col2:
        st.metric("Matched Skills", len(matched))

    with col3:
        st.metric("Missing Skills", len(missing))

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Matched Skills")
        if matched:
            for skill in matched:
                st.success(skill)
        else:
            st.info("No matched skills found.")

    with col2:
        st.markdown("### Missing Skills")
        if missing:
            for skill in missing:
                st.error(skill)
        else:
            st.success("No missing skills.")

    st.markdown("---")

    st.markdown("### Suggestions")
    if suggestions:
        for s in suggestions:
            st.info(s)
    else:
        st.info("No suggestions available.")


# =========================================================
# HEADER
# =========================================================

st.title("🚀 HireSense AI")
st.subheader("Universal Resume Optimizer & Career Toolkit")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("### Select Your Field")

    selected_field_name = st.selectbox(
        "Choose a field:",
        list(fields_data.keys())
    )

    selected_field_data = fields_data[selected_field_name]
    selected_field_id = selected_field_data["id"]

    st.markdown("### Select Your Role")

    selected_role = st.selectbox(
        "Choose a role:",
        selected_field_data["roles"]
    )

    st.markdown("---")
    st.success(f"Field: {selected_field_name}")
    st.success(f"Role: {selected_role}")

    st.markdown("---")
    st.markdown("### Supported Features")
    st.markdown("""
    - Resume scoring
    - ATS suggestions
    - Single job matching
    - Multi-job comparison
    - Resume upload
    - Interview prep
    - Salary insights
    """)

# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 Resume Optimizer",
    "📊 Job Matcher",
    "🔄 Compare Jobs",
    "🎤 Interview Prep",
    "📈 Market Insights"
])

# =========================================================
# TAB 1: RESUME OPTIMIZER
# =========================================================

with tab1:
    st.markdown("## 📄 Resume Optimizer & ATS Checker")
    st.markdown(f"Optimizing for **{selected_field_name} - {selected_role}**")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Your Resume")

        resume_input_method = st.radio(
            "Resume input method:",
            ["Paste Text", "Upload File"],
            horizontal=True,
            key="optimizer_resume_method"
        )

        resume_text = ""

        if resume_input_method == "Paste Text":
            resume_text = st.text_area(
                "Paste your resume:",
                height=350,
                placeholder="Paste your complete resume here...",
                key="optimizer_resume_text"
            )
        else:
            uploaded_resume = st.file_uploader(
                "Upload resume:",
                type=["txt", "pdf", "docx", "doc"],
                key="optimizer_resume_file"
            )

            if uploaded_resume:
                resume_text = extract_text_from_file(uploaded_resume)

                if resume_text:
                    st.success(f"Uploaded: {uploaded_resume.name}")
                    with st.expander("Preview extracted text"):
                        st.text_area(
                            "Extracted Resume Text",
                            value=resume_text[:1500],
                            height=200,
                            disabled=True
                        )
                else:
                    st.error("Could not extract resume text. Please paste it manually.")

    with col2:
        st.markdown("### Job Description Optional")
        jd_text = st.text_area(
            "Paste job description for targeted optimization:",
            height=350,
            placeholder="Optional: paste a job description here...",
            key="optimizer_jd_text"
        )

    st.markdown("---")

    if st.button("🚀 Analyze & Optimize Resume", use_container_width=True):
        if not resume_text.strip():
            st.warning("Please provide your resume first.")
        else:
            result = score_resume_universal(resume_text, selected_field_data)

            st.success("Resume analysis complete.")
            st.markdown("---")

            score = result["score"]

            if score >= 80:
                score_color = "#28a745"
                score_label = "Strong"
            elif score >= 60:
                score_color = "#ffc107"
                score_label = "Good"
            else:
                score_color = "#dc3545"
                score_label = "Needs Work"

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    f"""
                    <div class="score-box" style="background:{score_color};">
                        <div style="font-size:42px;">{score}/100</div>
                        <div>{score_label} Resume Score</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.metric("ATS Compatibility", f"{result['ats_score']}%")
                st.metric("Word Count", result["word_count"])

            with col3:
                st.metric("Matched Skills", len(result["matched_skills"]))
                st.metric("Missing Skills", len(result["missing_skills"]))

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Strengths")
                if result["strengths"]:
                    for s in result["strengths"]:
                        st.success(s)
                else:
                    st.info("No major strengths detected yet.")

            with col2:
                st.markdown("### Issues")
                if result["issues"]:
                    for issue in result["issues"]:
                        st.warning(issue)
                else:
                    st.success("No major issues found.")

            st.markdown("---")

            st.markdown("### Improvement Suggestions")
            if result["improvements"]:
                for imp in result["improvements"]:
                    st.info(imp)
            else:
                st.success("Your resume looks well optimized.")

            st.markdown("---")

            if jd_text.strip():
                st.markdown("### Job Description Match")
                try:
                    match_data = call_match_api(resume_text, jd_text)
                    render_match_results(match_data)
                except Exception as e:
                    st.error(f"Could not match with job description: {e}")

            st.markdown("---")

            report = f"""
HIRESENSE AI - RESUME OPTIMIZATION REPORT
=========================================

Field: {selected_field_name}
Role: {selected_role}

Resume Score: {result['score']}/100
ATS Compatibility: {result['ats_score']}%
Word Count: {result['word_count']}

Matched Skills:
{', '.join(result['matched_skills'])}

Missing Skills:
{', '.join(result['missing_skills'])}

Strengths:
{chr(10).join('- ' + s for s in result['strengths'])}

Issues:
{chr(10).join('- ' + i for i in result['issues'])}

Improvement Suggestions:
{chr(10).join('- ' + i for i in result['improvements'])}

Generated by HireSense AI
"""

            st.download_button(
                "📥 Download Resume Report",
                report,
                "resume_optimization_report.txt",
                "text/plain",
                use_container_width=True
            )

# =========================================================
# TAB 2: JOB MATCHER
# =========================================================

with tab2:
    st.markdown("## 📊 Single Job Matcher")
    st.markdown("Compare your resume against one job description.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Resume")

        method = st.radio(
            "Resume input:",
            ["Paste Text", "Upload File"],
            horizontal=True,
            key="single_resume_method"
        )

        single_resume = ""

        if method == "Paste Text":
            single_resume = st.text_area(
                "Paste resume:",
                height=300,
                key="single_resume_text"
            )
        else:
            file = st.file_uploader(
                "Upload resume:",
                type=["txt", "pdf", "docx", "doc"],
                key="single_resume_file"
            )

            if file:
                single_resume = extract_text_from_file(file)
                if single_resume:
                    st.success(f"Uploaded: {file.name}")

    with col2:
        st.markdown("### Job Description")

        jd_method = st.radio(
            "JD input:",
            ["Paste Text", "Upload File"],
            horizontal=True,
            key="single_jd_method"
        )

        single_jd = ""

        if jd_method == "Paste Text":
            single_jd = st.text_area(
                "Paste job description:",
                height=300,
                key="single_jd_text"
            )
        else:
            file = st.file_uploader(
                "Upload job description:",
                type=["txt", "pdf", "docx", "doc"],
                key="single_jd_file"
            )

            if file:
                single_jd = extract_text_from_file(file)
                if single_jd:
                    st.success(f"Uploaded: {file.name}")

    st.markdown("---")

    if st.button("🔍 Analyze Match", use_container_width=True):
        if not single_resume.strip() or not single_jd.strip():
            st.warning("Please provide both resume and job description.")
        else:
            with st.spinner("Analyzing match..."):
                try:
                    data = call_match_api(single_resume, single_jd)
                    st.success("Analysis complete.")
                    render_match_results(data)
                except Exception as e:
                    st.error(f"Error: {e}")

# =========================================================
# TAB 3: COMPARE JOBS
# =========================================================

with tab3:
    st.markdown("## 🔄 Compare Resume Against Multiple Jobs")
    st.markdown("Upload or paste your resume once, then compare it against 2-5 job descriptions.")
    st.markdown("---")

    st.markdown("### Resume")

    compare_resume_method = st.radio(
        "Resume input method:",
        ["Paste Text", "Upload File"],
        horizontal=True,
        key="compare_resume_method"
    )

    compare_resume = ""

    if compare_resume_method == "Paste Text":
        compare_resume = st.text_area(
            "Paste your resume:",
            height=250,
            key="compare_resume_text"
        )
    else:
        uploaded_resume = st.file_uploader(
            "Upload resume:",
            type=["txt", "pdf", "docx", "doc"],
            key="compare_resume_file"
        )

        if uploaded_resume:
            compare_resume = extract_text_from_file(uploaded_resume)

            if compare_resume:
                st.success(f"Uploaded: {uploaded_resume.name}")
                with st.expander("Preview extracted resume"):
                    st.text_area(
                        "Extracted Resume Text",
                        value=compare_resume[:1500],
                        height=200,
                        disabled=True
                    )
            else:
                st.error("Could not extract resume text. Please paste it manually.")

    st.markdown("---")

    st.markdown("### Job Descriptions")

    num_jobs = st.slider(
        "How many jobs do you want to compare?",
        min_value=2,
        max_value=5,
        value=2
    )

    job_descriptions = []

    for i in range(num_jobs):
        st.markdown(f"#### Job {i + 1}")

        job_method = st.radio(
            f"Job {i + 1} input method:",
            ["Paste Text", "Upload File"],
            horizontal=True,
            key=f"compare_job_method_{i}"
        )

        job_text = ""

        if job_method == "Paste Text":
            job_text = st.text_area(
                f"Paste Job {i + 1} description:",
                height=160,
                key=f"compare_job_text_{i}"
            )
        else:
            uploaded_job = st.file_uploader(
                f"Upload Job {i + 1} description:",
                type=["txt", "pdf", "docx", "doc"],
                key=f"compare_job_file_{i}"
            )

            if uploaded_job:
                job_text = extract_text_from_file(uploaded_job)

                if job_text:
                    st.success(f"Uploaded: {uploaded_job.name}")
                else:
                    st.error("Could not extract job description.")

        job_descriptions.append(job_text)
        st.divider()

    if st.button("🚀 Compare Against All Jobs", use_container_width=True):
        valid_jobs = [job for job in job_descriptions if job.strip()]

        if not compare_resume.strip():
            st.warning("Please provide your resume.")
        elif len(valid_jobs) < 2:
            st.warning("Please provide at least two job descriptions.")
        else:
            with st.spinner("Comparing your resume against all jobs..."):
                results = []

                for idx, job in enumerate(valid_jobs, start=1):
                    try:
                        data = call_match_api(compare_resume, job)
                        results.append({
                            "job_number": idx,
                            "match_score": data.get("match_score_percent", 0),
                            "matched_skills": data.get("matched_skills", []),
                            "missing_skills": data.get("missing_skills", []),
                            "suggestions": data.get("suggestions", [])
                        })
                    except Exception as e:
                        st.warning(f"Could not analyze Job {idx}: {e}")

                if results:
                    st.success("Comparison complete.")
                    st.markdown("---")

                    best_job = max(results, key=lambda x: x["match_score"])
                    worst_job = min(results, key=lambda x: x["match_score"])
                    avg_score = round(sum(r["match_score"] for r in results) / len(results), 2)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Best Match",
                            f"Job {best_job['job_number']}",
                            f"{best_job['match_score']}%"
                        )

                    with col2:
                        st.metric(
                            "Average Match",
                            f"{avg_score}%"
                        )

                    with col3:
                        st.metric(
                            "Lowest Match",
                            f"Job {worst_job['job_number']}",
                            f"{worst_job['match_score']}%"
                        )

                    st.markdown("---")

                    st.markdown("### Comparison Table")

                    table_data = []
                    for r in results:
                        table_data.append({
                            "Job": f"Job {r['job_number']}",
                            "Match Score": f"{r['match_score']}%",
                            "Matched Skills": len(r["matched_skills"]),
                            "Missing Skills": len(r["missing_skills"])
                        })

                    st.dataframe(table_data, use_container_width=True, hide_index=True)

                    st.markdown("---")

                    st.markdown("### Detailed Breakdown")

                    for r in results:
                        score = r["match_score"]

                        if score >= 80:
                            emoji = "🟢"
                            label = "Excellent Match"
                        elif score >= 60:
                            emoji = "🟡"
                            label = "Good Match"
                        elif score >= 40:
                            emoji = "🟠"
                            label = "Fair Match"
                        else:
                            emoji = "🔴"
                            label = "Low Match"

                        with st.expander(
                            f"{emoji} Job {r['job_number']} - {score}% - {label}",
                            expanded=(r["job_number"] == best_job["job_number"])
                        ):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("#### Matched Skills")
                                if r["matched_skills"]:
                                    for skill in r["matched_skills"]:
                                        st.success(skill)
                                else:
                                    st.info("No matched skills.")

                            with col2:
                                st.markdown("#### Missing Skills")
                                if r["missing_skills"]:
                                    for skill in r["missing_skills"]:
                                        st.error(skill)
                                else:
                                    st.success("No missing skills.")

                            st.markdown("#### Suggestions")
                            for s in r["suggestions"]:
                                st.info(s)

                    st.markdown("---")

                    st.markdown("### Recommendation")
                    st.success(
                        f"Your best fit is **Job {best_job['job_number']}** "
                        f"with a match score of **{best_job['match_score']}%**. "
                        f"Prioritize this role and tailor your resume toward its missing skills."
                    )

                    report = "HIRESENSE AI - MULTI JOB COMPARISON REPORT\n"
                    report += "==========================================\n\n"
                    report += f"Best Match: Job {best_job['job_number']} ({best_job['match_score']}%)\n"
                    report += f"Average Match: {avg_score}%\n"
                    report += f"Lowest Match: Job {worst_job['job_number']} ({worst_job['match_score']}%)\n\n"

                    for r in results:
                        report += f"Job {r['job_number']} - {r['match_score']}%\n"
                        report += f"Matched Skills: {', '.join(r['matched_skills'])}\n"
                        report += f"Missing Skills: {', '.join(r['missing_skills'])}\n\n"

                    st.download_button(
                        "📥 Download Comparison Report",
                        report,
                        "multi_job_comparison_report.txt",
                        "text/plain",
                        use_container_width=True
                    )

# =========================================================
# TAB 4: INTERVIEW PREP
# =========================================================

with tab4:
    st.markdown("## 🎤 Interview Preparation")
    st.markdown(f"Preparing for **{selected_field_name} - {selected_role}**")
    st.markdown("---")

    questions = {
        "IT": [
            ("Tell me about your biggest technical project.", "Explain the problem, your role, tech stack, impact, and measurable result."),
            ("How do you debug production issues?", "Discuss logs, monitoring, reproduction, root cause analysis, and prevention."),
            ("How do you write clean code?", "Mention readability, naming, testing, documentation, and refactoring."),
            ("Explain a system design challenge you solved.", "Discuss scale, tradeoffs, architecture, database, and deployment.")
        ],
        "Finance": [
            ("Walk me through a financial model.", "Explain assumptions, revenue, costs, margins, scenarios, and outputs."),
            ("How do you analyze risk?", "Talk about risk identification, measurement, mitigation, and monitoring."),
            ("Which financial ratios do you use?", "Mention ROE, ROA, P/E, debt-equity, current ratio depending on role.")
        ],
        "Marketing": [
            ("Describe a successful campaign.", "Explain goal, audience, channels, execution, metrics, and ROI."),
            ("How do you measure marketing success?", "Discuss CAC, LTV, CTR, conversion rate, ROAS, engagement."),
            ("How do you build a content strategy?", "Mention audience, positioning, channels, calendar, measurement.")
        ],
        "Design": [
            ("Walk me through your design process.", "Research, define, ideate, prototype, test, iterate."),
            ("How do you handle design feedback?", "Show collaboration, reasoning, user focus, and iteration."),
            ("Tell me about a UX problem you solved.", "Explain user pain, research insights, solution, and impact.")
        ],
        "HR": [
            ("How do you approach recruitment?", "Discuss sourcing, screening, interviews, candidate experience, offer closure."),
            ("How do you handle employee conflict?", "Mention listening, neutrality, policy, documentation, and resolution."),
            ("How do you improve retention?", "Talk about engagement, growth, feedback, recognition, and culture.")
        ],
        "Sales": [
            ("Describe your sales process.", "Prospecting, qualification, discovery, demo, negotiation, closing, follow-up."),
            ("How do you handle objections?", "Listen, clarify, empathize, reframe value, confirm resolution."),
            ("Tell me about your biggest deal.", "Discuss customer need, strategy, stakeholders, negotiation, outcome.")
        ],
        "Consulting": [
            ("How do you solve a business problem?", "Clarify objective, structure, analyze, recommend, communicate."),
            ("Walk me through a case approach.", "Use frameworks, assumptions, data, synthesis, and recommendation."),
            ("Tell me about client impact.", "Focus on business outcome, measurable improvement, and stakeholder management.")
        ],
        "Healthcare": [
            ("Why healthcare?", "Show empathy, service mindset, patient focus, and long-term commitment."),
            ("How do you handle difficult patients?", "Mention empathy, communication, documentation, escalation if needed."),
            ("How do you stay updated?", "Medical journals, CME, guidelines, peer learning, continuous training.")
        ],
        "SupplyChain": [
            ("How do you optimize supply chain cost?", "Talk about demand planning, inventory control, vendor negotiation, logistics optimization."),
            ("How do you manage inventory risk?", "Mention safety stock, forecasting, lead times, ABC analysis, supplier reliability."),
            ("What tools have you used?", "SAP, ERP, Excel, Power BI, warehouse systems, procurement tools.")
        ],
        "RenewableEnergy": [
            ("Why renewable energy?", "Show passion for sustainability, climate impact, and energy transition."),
            ("Explain a solar or wind project.", "Discuss design, feasibility, cost, output, execution, and impact."),
            ("How do you measure project success?", "Mention capacity, efficiency, ROI, carbon reduction, and reliability.")
        ],
        "Law": [
            ("Describe your legal research process.", "Issue identification, statutes, precedents, analysis, and legal opinion."),
            ("How do you review contracts?", "Parties, obligations, risk clauses, liability, termination, compliance."),
            ("Tell me about a challenging legal matter.", "Explain facts, issue, approach, reasoning, and outcome.")
        ]
    }

    field_questions = questions.get(selected_field_id, questions["IT"])

    for idx, (question, answer_tip) in enumerate(field_questions, start=1):
        with st.expander(f"Q{idx}: {question}"):
            st.markdown("### Answer Strategy")
            st.info(answer_tip)
            st.markdown("### General Tip")
            st.markdown("Use the STAR method: Situation, Task, Action, Result.")

    st.markdown("---")

    st.markdown("## Universal Interview Checklist")
    st.markdown("""
    - Research the company.
    - Read the job description carefully.
    - Prepare 3-5 STAR stories.
    - Prepare salary expectations.
    - Prepare questions to ask the interviewer.
    - Practice your introduction.
    - Know your resume deeply.
    """)

# =========================================================
# TAB 5: MARKET INSIGHTS
# =========================================================

with tab5:
    st.markdown("## 📈 Salary & Market Insights")
    st.markdown(f"Market insights for **{selected_field_name} - {selected_role}**")
    st.markdown("---")

    salary = selected_field_data.get("salary", {})
    cities = selected_field_data.get("cities", {})
    career_path = selected_field_data.get("path", "Entry → Mid → Senior → Lead")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Salary Ranges")

        for level, value in salary.items():
            st.metric(level, value)

    with col2:
        st.markdown("### City Salary Multiplier")

        if cities:
            selected_city = st.selectbox(
                "Choose city:",
                list(cities.keys())
            )

            multiplier = cities[selected_city]
            st.info(f"{selected_city} typically pays around **{multiplier}x** relative to baseline market salaries.")

        else:
            st.info("City data not available for this field.")

    st.markdown("---")

    st.markdown("### Career Growth Path")
    st.success(career_path)

    st.markdown("---")

    st.markdown("### Job Posting Red Flags")
    red_flags = [
        "No clear salary range.",
        "Very vague job responsibilities.",
        "Too many roles combined into one position.",
        "Unrealistic experience requirements for entry-level roles.",
        "High pressure language without clear benefits.",
        "No information about growth, team, or reporting structure."
    ]

    for flag in red_flags:
        st.warning(flag)

    st.markdown("---")

    st.markdown("### Green Flags")
    green_flags = [
        "Clear responsibilities and expectations.",
        "Transparent compensation range.",
        "Defined growth path.",
        "Good learning and mentorship opportunities.",
        "Strong company reputation.",
        "Healthy work-life balance indicators."
    ]

    for flag in green_flags:
        st.success(flag)

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:gray;'>"
    "<small>HireSense AI | Universal Career Optimizer | Multi-field Resume, Job, Interview & Market Toolkit</small>"
    "</div>",
    unsafe_allow_html=True
)