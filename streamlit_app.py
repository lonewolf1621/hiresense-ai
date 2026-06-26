import streamlit as st
import requests

st.set_page_config(
    page_title="HireSense AI - Universal Career Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white; font-weight: bold; border-radius: 8px; padding: 12px 30px;
    }
    h1 { color: #667eea; text-align: center; }
    h2 { color: #764ba2; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

API_URL = "https://hiresense-ai-3k4d.onrender.com/analyze"

st.title("🚀 HireSense AI")
st.subheader("Universal Resume Optimizer & Career Toolkit")

# FIELD & ROLE DATA (Embedded)
fields_data = {
    "💻 Information Technology": {
        "id": "IT",
        "roles": ["Backend Developer", "Frontend Developer", "Full Stack Developer", "DevOps Engineer", "Data Engineer", "ML Engineer"],
        "skills": ["Python", "Java", "AWS", "Docker", "React", "SQL"],
        "keywords": ["Development", "Software", "Engineering", "Cloud", "Database"]
    },
    "💰 Finance & Banking": {
        "id": "Finance",
        "roles": ["Investment Banker", "Financial Analyst", "Risk Manager", "Portfolio Manager"],
        "skills": ["Excel", "Financial Modeling", "Risk Analysis", "Bloomberg"],
        "keywords": ["Analysis", "Investment", "Banking", "Risk", "Portfolio"]
    },
    "📊 Marketing & Advertising": {
        "id": "Marketing",
        "roles": ["Digital Marketing Manager", "Content Strategist", "Brand Manager", "SEO Specialist"],
        "skills": ["Google Analytics", "SEO", "Content Strategy", "Salesforce"],
        "keywords": ["Campaign", "Strategy", "Digital", "Analytics", "Brand"]
    },
    "🎨 Design & UX": {
        "id": "Design",
        "roles": ["Product Designer", "UX Designer", "UI Designer", "Design Lead"],
        "skills": ["Figma", "Adobe XD", "Prototyping", "User Research"],
        "keywords": ["Design", "User Experience", "Interface", "Prototype"]
    },
    "👥 Human Resources": {
        "id": "HR",
        "roles": ["Recruiter", "HR Manager", "Talent Acquisition", "HR Business Partner"],
        "skills": ["HRIS", "Recruitment", "ATS", "Employee Relations"],
        "keywords": ["Recruitment", "HR", "Talent", "Employee", "Culture"]
    },
    "📈 Sales": {
        "id": "Sales",
        "roles": ["Sales Executive", "Account Manager", "Sales Manager", "Business Development"],
        "skills": ["Salesforce", "CRM", "Negotiation", "Pipeline Management"],
        "keywords": ["Sales", "Revenue", "Account", "Customer", "Growth"]
    },
    "📋 Consulting": {
        "id": "Consulting",
        "roles": ["Management Consultant", "Business Analyst", "Strategy Consultant"],
        "skills": ["Problem Solving", "PowerPoint", "Data Analysis"],
        "keywords": ["Consulting", "Strategy", "Analysis", "Implementation"]
    },
    "⚕️ Healthcare": {
        "id": "Healthcare",
        "roles": ["Doctor", "Nurse", "Healthcare Administrator", "Pharmacist"],
        "skills": ["Patient Care", "Medical Knowledge", "EHR"],
        "keywords": ["Healthcare", "Medical", "Patient", "Clinical"]
    }
}

# SIDEBAR
with st.sidebar:
    st.markdown("### 🎯 Select Your Field")
    selected_field_display = st.selectbox("Choose field:", list(fields_data.keys()), key="field")
    selected_field_data = fields_data[selected_field_display]
    selected_field = selected_field_data["id"]
    
    st.markdown("### 💼 Select Your Role")
    selected_role = st.selectbox("Choose role:", selected_field_data["roles"], key="role")
    
    st.markdown("---")
    st.success(f"**Field:** {selected_field_display}")
    st.success(f"**Role:** {selected_role}")

# TABS
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Resume Optimizer",
    "📊 Job Matcher",
    "🎤 Interview Prep",
    "📈 Market Insights"
])

# ===== TAB 1: RESUME OPTIMIZER =====
with tab1:
    st.markdown("## 📄 Resume Optimizer & ATS Checker")
    st.markdown(f"*Optimizing for **{selected_field_display} - {selected_role}***")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📤 Your Resume")
        resume = st.text_area("Paste resume:", height=350, key="resume_opt")
    
    with col2:
        st.markdown("### 💼 Job Description (Optional)")
        jd = st.text_area("Paste JD:", height=350, key="jd_opt")
    
    if st.button("🚀 Analyze & Score", use_container_width=True):
        if not resume:
            st.warning("⚠️ Paste your resume first")
        else:
            with st.spinner("Analyzing..."):
                # SCORING LOGIC
                score = 0
                issues = []
                improvements = []
                strengths = []
                
                resume_lower = resume.lower()
                word_count = len(resume.split())
                
                # Length check
                if 300 <= word_count <= 800:
                    score += 15
                    strengths.append("✅ Optimal resume length")
                else:
                    issues.append("Resume length not optimal")
                    improvements.append("📝 Aim for 300-800 words")
                
                # Contact info
                if "@" in resume and any(c.isdigit() for c in resume):
                    score += 10
                    strengths.append("✅ Contact info present")
                else:
                    issues.append("Missing contact info")
                    improvements.append("📧 Add email and phone")
                
                # Field-specific skills
                skills = selected_field_data["skills"]
                found_skills = [s for s in skills if s.lower() in resume_lower]
                
                if found_skills:
                    score += min((len(found_skills) / len(skills)) * 30, 30)
                    strengths.append(f"✅ Found {len(found_skills)} key skills")
                else:
                    issues.append("Missing field skills")
                    improvements.append(f"🎯 Add: {', '.join(skills[:3])}")
                
                # Action verbs
                action_verbs = ["led", "managed", "developed", "created", "improved", "built", "launched"]
                action_count = sum(1 for v in action_verbs if v in resume_lower)
                
                if action_count > 5:
                    score += 20
                    strengths.append("✅ Strong action verbs")
                else:
                    issues.append("Weak language")
                    improvements.append("💪 Use: Led, Built, Achieved, Created")
                
                # Metrics
                import re
                numbers = re.findall(r'\d+[%+x]?', resume_lower)
                
                if len(numbers) > 5:
                    score += 15
                    strengths.append(f"✅ Good metrics ({len(numbers)} found)")
                else:
                    improvements.append("📊 Add numbers: 'Increased by 40%', 'Managed $2M'")
                
                # Keywords
                keywords = selected_field_data["keywords"]
                found_keywords = [k for k in keywords if k.lower() in resume_lower]
                
                if found_keywords:
                    score += 10
                    strengths.append(f"✅ Industry keywords: {', '.join(found_keywords)}")
                
                final_score = min(score, 100)
                
                # DISPLAY RESULTS
                st.success("✅ Analysis Complete!")
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    color = "#28a745" if final_score >= 80 else "#ffc107" if final_score >= 60 else "#dc3545"
                    st.markdown(f"""
                    <div style='background: {color}; color: white; padding: 30px; border-radius: 10px; text-align: center;'>
                    <h2 style='color: white; margin: 0;'>{final_score}/100</h2>
                    <p style='margin: 0;'>Resume Score</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    ats = round((final_score / 100) * 100)
                    st.metric("🤖 ATS Score", f"{ats}%")
                
                with col3:
                    st.metric("📝 Word Count", word_count)
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ✅ Strengths")
                    for s in strengths:
                        st.success(s)
                
                with col2:
                    st.markdown("### ⚠️ Issues")
                    if issues:
                        for i in issues:
                            st.warning(i)
                    else:
                        st.success("No issues!")
                
                st.markdown("---")
                st.markdown("### 💡 Improvements")
                for imp in improvements:
                    st.info(imp)
                
                st.markdown("---")
                
                # JD MATCHING
                if jd:
                    st.markdown("### 🎯 Job Match")
                    with st.spinner("Matching..."):
                        try:
                            r = requests.post(API_URL, json={"resume": resume, "job_description": jd}, timeout=30)
                            if r.status_code == 200:
                                data = r.json()
                                st.metric("Job Match", f"{data['match_score_percent']}%")
                                st.markdown(f"**Matched:** {', '.join(data['matched_skills'][:5])}")
                        except:
                            st.info("Job matching unavailable")

# ===== TAB 2: JOB MATCHER =====
with tab2:
    st.markdown("## 📊 Job Matcher")
    col1, col2 = st.columns(2)
    
    with col1:
        resume = st.text_area("Resume:", height=300, key="match_resume")
    with col2:
        jd = st.text_area("Job Description:", height=300, key="match_jd")
    
    if st.button("🔍 Match", use_container_width=True):
        if resume and jd:
            with st.spinner("Analyzing..."):
                try:
                    r = requests.post(API_URL, json={"resume": resume, "job_description": jd}, timeout=30)
                    if r.status_code == 200:
                        data = r.json()
                        st.success("✅ Done!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1: st.metric("Match %", f"{data['match_score_percent']}%")
                        with col2: st.metric("Matched", len(data['matched_skills']))
                        with col3: st.metric("Missing", len(data['missing_skills']))
                        
                        st.markdown("---")
                        st.markdown(f"**✅ Matched:** {', '.join(data['matched_skills'])}")
                        st.markdown(f"**❌ Missing:** {', '.join(data['missing_skills'])}")
                        
                        st.markdown("---")
                        for s in data['suggestions']:
                            st.info(s)
                except:
                    st.error("Error analyzing")
        else:
            st.warning("Fill both fields")

# ===== TAB 3: INTERVIEW PREP =====
with tab3:
    st.markdown(f"## 🎤 Interview Prep for {selected_field}")
    
    questions = {
        "IT": [
            ("Tell me about your biggest project", "Use STAR method. Explain problem, your role, actions, and results."),
            ("How do you handle debugging?", "Explain systematic approach: logs, testing, version control."),
            ("What's your experience with cloud platforms?", "Discuss AWS/Azure/GCP experience with specific examples."),
            ("How do you write clean code?", "Discuss naming, comments, refactoring, and testing practices.")
        ],
        "Finance": [
            ("Explain a financial ratio you use", "Show understanding of key metrics like ROE, P/E ratio."),
            ("Walk me through a financial model", "Show ability to build and analyze financial projections."),
            ("How do you stay updated on markets?", "Discuss news sources, analysis, and learning approach.")
        ],
        "Marketing": [
            ("Describe a successful campaign", "Show strategy, execution, metrics, and ROI."),
            ("How do you measure campaign success?", "Discuss KPIs: CTR, conversion, CAC, LTV."),
            ("What's your approach to content strategy?", "Explain audience, channels, planning, execution.")
        ],
        "Design": [
            ("Walk through your design process", "Research → Wireframe → Design → Test → Iterate"),
            ("How do you handle feedback?", "Show openness, professionalism, and improvement mindset."),
            ("Tell me about a UX challenge", "Show problem-solving and user-centric thinking.")
        ],
        "HR": [
            ("How do you approach recruitment?", "Show strategic sourcing, screening, and interview process."),
            ("Handle a difficult employee situation", "Show conflict resolution, fairness, documentation."),
            ("What's your approach to retention?", "Discuss engagement, development, culture.")
        ],
        "Sales": [
            ("Describe your sales approach", "Show methodology: prospecting, qualification, closing."),
            ("How do you handle objections?", "Show problem-solving and value communication."),
            ("Tell me about your biggest deal", "Show process, relationship building, negotiation.")
        ],
        "Consulting": [
            ("Solve this case study", "Structure: understand, analyze, recommend, communicate."),
            ("How do you approach new problems?", "Show analytical thinking and problem-solving."),
            ("Tell me about client impact", "Show results, insights, and business value delivered.")
        ],
        "Healthcare": [
            ("Why healthcare?", "Show genuine passion and commitment to patient care."),
            ("Handle a difficult patient situation", "Show empathy, professionalism, communication."),
            ("Stay updated with medical advances?", "Show commitment to continuous learning.")
        ]
    }
    
    field_questions = questions.get(selected_field, questions["IT"])
    
    for i, (q, a) in enumerate(field_questions, 1):
        with st.expander(f"Q{i}: {q}"):
            st.markdown(f"**Answer Tips:**\n{a}")

# ===== TAB 4: MARKET INSIGHTS =====
with tab4:
    st.markdown(f"## 📈 Salary & Market for {selected_field}")
    
    salary_ranges = {
        "IT": {"Entry": "₹5-15 LPA", "Mid": "₹15-40 LPA", "Senior": "₹40-80 LPA", "Lead": "₹80-150+ LPA"},
        "Finance": {"Entry": "₹8-20 LPA", "Mid": "₹20-60 LPA", "Senior": "₹60-150 LPA", "Lead": "₹150-300+ LPA"},
        "Marketing": {"Entry": "₹5-12 LPA", "Mid": "₹12-40 LPA", "Senior": "₹40-80 LPA", "Lead": "₹80-150+ LPA"},
        "Design": {"Entry": "₹6-15 LPA", "Mid": "₹15-40 LPA", "Senior": "₹40-80 LPA", "Lead": "₹80-120+ LPA"},
        "HR": {"Entry": "₹5-12 LPA", "Mid": "₹12-30 LPA", "Senior": "₹30-60 LPA", "Lead": "₹60-100+ LPA"},
        "Sales": {"Entry": "₹6-15 LPA", "Mid": "₹15-50 LPA", "Senior": "₹50-100 LPA", "Lead": "₹100-200+ LPA"},
        "Consulting": {"Entry": "₹10-25 LPA", "Mid": "₹25-70 LPA", "Senior": "₹70-150 LPA", "Lead": "₹150-300+ LPA"},
        "Healthcare": {"Entry": "₹6-15 LPA", "Mid": "₹15-40 LPA", "Senior": "₹40-80 LPA", "Lead": "₹80-150+ LPA"}
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Salary Ranges")
        ranges = salary_ranges.get(selected_field, salary_ranges["IT"])
        for level, sal in ranges.items():
            st.metric(level, sal)
    
    with col2:
        st.markdown("### 📍 City Multipliers")
        cities = {
            "Bangalore": 1.3,
            "Mumbai": 1.3,
            "Delhi NCR": 1.2,
            "Hyderabad": 1.15,
            "Pune": 1.1
        }
        city = st.selectbox("Select city:", list(cities.keys()))
        mult = cities[city]
        st.info(f"💰 {city} multiplier: **{mult}x** base salary")
    
    st.markdown("---")
    st.markdown("### 🚀 Career Growth Path")
    paths = {
        "IT": "Junior → Mid → Senior → Lead → Architect",
        "Finance": "Analyst → Associate → VP → Director → MD",
        "Marketing": "Associate → Manager → Senior → Director → VP",
        "Design": "Junior Designer → Designer → Senior → Lead → Head",
        "HR": "Associate → Manager → Senior Manager → Director → VP",
        "Sales": "Associate → Manager → Regional → Director → VP",
        "Consulting": "Analyst → Consultant → Manager → Principal → Partner",
        "Healthcare": "Resident → Specialist → Senior → Head → Director"
    }
    st.success(paths.get(selected_field, "Entry → Mid → Senior → Lead"))

st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'><small>HireSense AI v2.1 | Multi-Field Career Optimizer</small></div>", unsafe_allow_html=True)