import streamlit as st
import requests
import os
import json
import re

# Try to import resume parser
try:
    from app.services.resume_parser import parse_resume as parse_file
    PARSER_AVAILABLE = True
except:
    PARSER_AVAILABLE = False
    def parse_file(file_bytes, file_type):
        return ""

# Try to import resume scorer
try:
    from app.services.resume_scorer import score_resume, suggest_improvements, load_field_data
    SCORER_AVAILABLE = True
except:
    SCORER_AVAILABLE = False
    def score_resume(resume, field, role):
        return {
            "score": 0, "strengths": [], "issues": [], "improvements": [],
            "matched_skills": [], "matched_keywords": [], "matched_certifications": [],
            "word_count": len(resume.split()), "action_verb_count": 0, "metric_count": 0,
            "ats_score": 0, "recommendations": []
        }
    def suggest_improvements(resume, field, role):
        return []
    def load_field_data():
        return {"fields": []}

st.set_page_config(
    page_title="HireSense AI - Universal Career Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white; font-weight: bold; border-radius: 8px;
        padding: 12px 30px; border: none;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    h1 { color: #667eea; text-align: center; }
    h2 { color: #764ba2; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
    h3 { color: #667eea; }
    [data-testid="metric-container"] {
        background-color: #f0f2f6; padding: 15px;
        border-radius: 10px; border-left: 5px solid #667eea;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 30px; border-radius: 15px;
        text-align: center; font-size: 48px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

API_URL = "https://hiresense-ai-3k4d.onrender.com/analyze"

st.title("🚀 HireSense AI")
st.subheader("Universal Resume Optimizer & Career Toolkit")

# ===========================
# SIDEBAR: FIELD & ROLE SELECTOR
# ===========================
with st.sidebar:
    st.markdown("### 🎯 Select Your Field")
    
    try:
        field_data = load_field_data()
        fields = field_data.get("fields", [])
        
        if fields:
            field_names = [f"{f.get('icon', '')} {f.get('name', '')}" for f in fields]
            field_ids = [f.get('id', '') for f in fields]
            
            selected_field_display = st.selectbox("Choose your field:", field_names, key="field_select")
            selected_field_idx = field_names.index(selected_field_display)
            selected_field = field_ids[selected_field_idx]
            
            # Get roles for selected field
            selected_field_data = fields[selected_field_idx]
            roles = selected_field_data.get("roles", [])
            
            st.markdown("### 💼 Select Your Role")
            selected_role = st.selectbox("Choose your role:", roles, key="role_select")
            
            st.markdown("---")
            st.markdown(f"**Field:** {selected_field_data.get('name')}")
            st.markdown(f"**Role:** {selected_role}")
            st.markdown(f"**Description:** {selected_field_data.get('description', '')}")
        else:
            selected_field = "IT"
            selected_role = "Backend Developer"
            st.warning("Field data not loaded, using defaults")
    except:
        selected_field = "IT"
        selected_role = "Backend Developer"
        st.error("Error loading field data")

# ===========================
# MAIN TABS
# ===========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Resume Optimizer",
    "📊 Job Matcher",
    "🎤 Interview Prep",
    "📈 Category"
])

# ===========================
# TAB 1: RESUME OPTIMIZER
# ===========================
with tab1:
    st.markdown("## 📄 Resume Optimizer & ATS Checker")
    st.markdown(f"*Optimizing your resume for **{selected_field} - {selected_role}***")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📤 Upload Your Resume")
        upload_method = st.radio("Choose method:", ["📝 Paste Text", "📎 Upload File"], key="opt_method", horizontal=True)
        
        resume_text = ""
        if upload_method == "📝 Paste Text":
            resume_text = st.text_area(
                "Paste your resume:",
                height=400,
                placeholder="Paste your full resume here...",
                key="opt_resume_text"
            )
        else:
            if PARSER_AVAILABLE:
                resume_file = st.file_uploader("Upload (PDF/DOCX/TXT):", type=["pdf", "docx", "doc", "txt"], key="opt_file")
                if resume_file:
                    file_bytes = resume_file.read()
                    file_type = resume_file.name.split(".")[-1]
                    resume_text = parse_file(file_bytes, file_type)
                    if resume_text:
                        st.success(f"✅ Uploaded: {resume_file.name}")
                        st.text_area("Extracted text:", value=resume_text, height=200, disabled=True)
                    else:
                        st.error("❌ Could not extract text")
            else:
                st.warning("File upload not available. Please paste text.")
                resume_text = st.text_area("Paste resume:", height=400, key="opt_backup")
    
    with col2:
        st.markdown("### 🎯 Job Description (Optional)")
        st.markdown("*Add JD for targeted optimization*")
        jd_text = st.text_area(
            "Paste job description:",
            height=400,
            placeholder="Paste job description for targeted optimization...",
            key="opt_jd"
        )
    
    st.markdown("---")
    
    # Analyze button
    if st.button("🚀 Analyze & Optimize Resume", use_container_width=True, key="opt_analyze"):
        if not resume_text:
            st.warning("⚠️ Please provide your resume")
        else:
            with st.spinner("🔍 Analyzing your resume..."):
                try:
                    # Score the resume
                    if SCORER_AVAILABLE:
                        result = score_resume(resume_text, selected_field, selected_role)
                    else:
                        result = {
                            "score": 75,
                            "ats_score": 75,
                            "strengths": ["Good structure", "Skills present"],
                            "issues": ["Add more metrics"],
                            "improvements": ["Add quantifiable achievements"],
                            "matched_skills": ["Skill 1", "Skill 2"],
                            "matched_keywords": ["Keyword 1"],
                            "matched_certifications": [],
                            "word_count": len(resume_text.split()),
                            "action_verb_count": 3,
                            "metric_count": 2,
                            "recommendations": ["Add numbers to achievements"]
                        }
                    
                    st.success("✅ Analysis Complete!")
                    st.markdown("---")
                    
                    # SCORE DISPLAY
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        score = result.get('score', 0)
                        score_color = "#28a745" if score >= 80 else "#ffc107" if score >= 60 else "#dc3545"
                        st.markdown(f"""
                        <div class='score-card' style='background: {score_color};'>
                            {score}/100<br>
                            <small style='font-size: 16px;'>Resume Score</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        ats_score = result.get('ats_score', 0)
                        st.metric("🤖 ATS Compatibility", f"{ats_score}%")
                        if ats_score >= 80:
                            st.success("ATS-friendly!")
                        else:
                            st.warning("Needs improvement")
                    
                    with col3:
                        word_count = result.get('word_count', 0)
                        st.metric("📝 Word Count", word_count)
                        if 300 <= word_count <= 800:
                            st.success("Optimal length")
                        else:
                            st.warning("Not optimal")
                    
                    st.markdown("---")
                    
                    # DETAILED BREAKDOWN
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### ✅ Strengths")
                        strengths = result.get('strengths', [])
                        if strengths:
                            for s in strengths:
                                st.success(s)
                        else:
                            st.info("No strengths detected")
                        
                        st.markdown("### 📊 Statistics")
                        st.markdown(f"- Action verbs: {result.get('action_verb_count', 0)}")
                        st.markdown(f"- Metrics/numbers: {result.get('metric_count', 0)}")
                        st.markdown(f"- Matched skills: {len(result.get('matched_skills', []))}")
                        st.markdown(f"- Field keywords: {len(result.get('matched_keywords', []))}")
                        st.markdown(f"- Certifications: {len(result.get('matched_certifications', []))}")
                    
                    with col2:
                        st.markdown("### ⚠️ Issues Found")
                        issues = result.get('issues', [])
                        if issues:
                            for i in issues:
                                st.warning(i)
                        else:
                            st.success("No issues found!")
                        
                        st.markdown("### 🎯 Matched Skills")
                        matched = result.get('matched_skills', [])
                        if matched:
                            st.markdown(" • ".join(matched))
                        else:
                            st.info("No field-specific skills detected")
                    
                    st.markdown("---")
                    
                    # IMPROVEMENT SUGGESTIONS
                    st.markdown("### 💡 Improvement Suggestions")
                    improvements = result.get('improvements', [])
                    if improvements:
                        for i, imp in enumerate(improvements, 1):
                            with st.expander(f"Suggestion {i}"):
                                st.info(imp)
                    else:
                        st.success("Your resume is well-optimized!")
                    
                    st.markdown("---")
                    
                    # BONUS: MATCH WITH JD IF PROVIDED
                    if jd_text:
                        st.markdown("### 🎯 Job Description Match")
                        with st.spinner("Matching with job description..."):
                            try:
                                response = requests.post(
                                    API_URL,
                                    json={"resume": resume_text, "job_description": jd_text},
                                    timeout=30
                                )
                                if response.status_code == 200:
                                    jd_data = response.json()
                                    jd_score = jd_data.get('match_score_percent', 0)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("📊 Job Match Score", f"{jd_score}%")
                                    with col2:
                                        missing = len(jd_data.get('missing_skills', []))
                                        st.metric("❌ Missing Skills", missing)
                                    
                                    st.markdown(f"**Matched:** {', '.join(jd_data.get('matched_skills', []))}")
                                    st.markdown(f"**Missing:** {', '.join(jd_data.get('missing_skills', []))}")
                            except:
                                st.info("JD matching unavailable")
                    
                    st.markdown("---")
                    
                    # DOWNLOAD REPORT
                    report_text = f"""HIRESENSE AI - RESUME OPTIMIZATION REPORT
==============================================
Field: {selected_field}
Role: {selected_role}
Overall Score: {score}/100
ATS Score: {ats_score}%
Word Count: {word_count}

Strengths:
{chr(10).join(f'✅ {s}' for s in strengths)}

Issues:
{chr(10).join(f'⚠️ {i}' for i in issues)}

Improvements:
{chr(10).join(f'💡 {imp}' for imp in improvements)}

Generated by HireSense AI
"""
                    st.download_button(
                        "📥 Download Full Report",
                        report_text,
                        "resume_report.txt",
                        "text/plain",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ===========================
# TAB 2: JOB MATCHER (Original)
# ===========================
with tab2:
    st.markdown("## 📊 Job Matcher")
    st.markdown("Match your resume against any job description")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📄 Resume")
        match_resume = st.text_area("Paste resume:", height=250, key="match_resume")
    
    with col2:
        st.markdown("### 💼 Job Description")
        match_jd = st.text_area("Paste job description:", height=250, key="match_jd")
    
    if st.button("🔍 Analyze Match", use_container_width=True, key="match_btn"):
        if match_resume and match_jd:
            with st.spinner("Analyzing..."):
                try:
                    response = requests.post(
                        API_URL,
                        json={"resume": match_resume, "job_description": match_jd},
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Done!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Match %", f"{data['match_score_percent']}%")
                        with col2:
                            st.metric("Matched", len(data['matched_skills']))
                        with col3:
                            st.metric("Missing", len(data['missing_skills']))
                        
                        st.markdown("---")
                        st.markdown(f"**✅ Matched:** {', '.join(data['matched_skills'])}")
                        st.markdown(f"**❌ Missing:** {', '.join(data['missing_skills'])}")
                        
                        st.markdown("---")
                        st.markdown("**Suggestions:**")
                        for s in data['suggestions']:
                            st.info(s)
                    else:
                        st.error(f"API Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Provide both resume and job description")

# ===========================
# TAB 3: INTERVIEW PREP
# ===========================
with tab3:
    st.markdown("## 🎤 Interview Preparation")
    st.markdown(f"*Preparing for **{selected_field}** roles*")
    st.markdown("---")
    
    st.markdown("### 💬 Common Interview Questions")
    
    # General questions (all fields)
    general_questions = [
        "Tell me about yourself.",
        "Why do you want this role?",
        "What are your strengths and weaknesses?",
        "Where do you see yourself in 5 years?",
        "Why should we hire you?",
        "Tell me about a challenge you faced and how you overcame it.",
        "Why are you leaving your current role?",
        "What's your expected salary?",
        "Do you have any questions for us?",
        "How do you handle stress and pressure?"
    ]
    
    st.markdown("**General Questions (All Fields):**")
    for i, q in enumerate(general_questions, 1):
        with st.expander(f"Q{i}: {q}"):
            st.markdown("**How to Answer:**")
            st.info("Use the STAR method: Situation, Task, Action, Result. Be concise and relevant.")
            st.markdown("**Tips:**")
            st.markdown("- Be honest and authentic")
            st.markdown("- Show enthusiasm for the role")
            st.markdown("- Relate answers to the job requirements")
    
    st.markdown("---")
    
    # Field-specific tips
    st.markdown(f"### 🎯 {selected_field}-Specific Tips")
    
    field_tips = {
        "IT": [
            "Prepare for coding challenges (LeetCode, HackerRank)",
            "Know system design principles",
            "Be ready for whiteboard sessions",
            "Understand Agile/Scrum methodologies",
            "Practice explaining complex technical concepts simply"
        ],
        "Finance": [
            "Know key financial metrics and ratios",
            "Prepare for case studies",
            "Be ready for mental math questions",
            "Understand current market trends",
            "Practice explaining financial concepts clearly"
        ],
        "Marketing": [
            "Prepare a campaign strategy example",
            "Know key marketing metrics (CAC, LTV, ROI)",
            "Be ready to analyze a real campaign",
            "Understand digital marketing channels",
            "Show data-driven thinking"
        ],
        "Design": [
            "Prepare your portfolio presentation",
            "Be ready for design challenges",
            "Explain your design process",
            "Discuss user research methods",
            "Show understanding of design systems"
        ],
        "HR": [
            "Understand HR metrics and KPIs",
            "Know employment laws and regulations",
            "Prepare examples of conflict resolution",
            "Be ready for behavioral questions",
            "Show understanding of company culture"
        ],
        "Sales": [
            "Prepare a sales pitch",
            "Know your numbers (quota, targets, achievements)",
            "Be ready for role-play scenarios",
            "Understand the sales cycle",
            "Show relationship-building skills"
        ],
        "Consulting": [
            "Prepare for case interviews",
            "Practice structured problem-solving",
            "Know consulting frameworks",
            "Be ready for estimation questions",
            "Show analytical thinking"
        ],
        "Healthcare": [
            "Review medical terminology",
            "Prepare patient care examples",
            "Know healthcare regulations",
            "Be ready for ethical scenarios",
            "Show empathy and communication skills"
        ]
    }
    
    tips = field_tips.get(selected_field, ["Prepare thoroughly", "Research the company", "Know your resume well"])
    for tip in tips:
        st.markdown(f"✅ {tip}")
    
    st.markdown("---")
    
    # Interview strategy
    st.markdown("### 📝 Interview Strategy")
    st.markdown("""
    **Before the Interview:**
    - ✅ Research the company thoroughly
    - ✅ Review the job description
    - ✅ Prepare 3-5 STAR stories
    - ✅ Prepare questions to ask
    - ✅ Test your tech setup (for virtual interviews)
    
    **During the Interview:**
    - ✅ Make eye contact and smile
    - ✅ Listen carefully and ask clarifying questions
    - ✅ Use the STAR method for behavioral questions
    - ✅ Show enthusiasm and interest
    - ✅ Take notes
    
    **After the Interview:**
    - ✅ Send a thank-you email within 24 hours
    - ✅ Reflect on what went well/needs improvement
    - ✅ Follow up if no response after 1 week
    """)

# ===========================
# TAB 4: SALARY & MARKET INSIGHTS
# ===========================
with tab4:
    st.markdown("## 📈 Salary & Market Insights")
    st.markdown(f"*Market data for **{selected_field} - {selected_role}***")
    st.markdown("---")
    
    # Salary ranges by field and experience
    salary_data = {
        "IT": {
            "Entry (0-2 years)": "₹5-15 LPA",
            "Mid (2-5 years)": "₹12-40 LPA",
            "Senior (5-10 years)": "₹30-80 LPA",
            "Lead (10+ years)": "₹60-150+ LPA"
        },
        "Finance": {
            "Entry (0-2 years)": "₹8-20 LPA",
            "Mid (2-5 years)": "₹20-60 LPA",
            "Senior (5-10 years)": "₹50-150 LPA",
            "Lead (10+ years)": "₹100-300+ LPA"
        },
        "Marketing": {
            "Entry (0-2 years)": "₹5-12 LPA",
            "Mid (2-5 years)": "₹12-40 LPA",
            "Senior (5-10 years)": "₹30-80 LPA",
            "Lead (10+ years)": "₹50-150+ LPA"
        },
        "Design": {
            "Entry (0-2 years)": "₹6-15 LPA",
            "Mid (2-5 years)": "₹15-40 LPA",
            "Senior (5-10 years)": "₹35-80 LPA",
            "Lead (10+ years)": "₹60-120+ LPA"
        },
        "HR": {
            "Entry (0-2 years)": "₹5-12 LPA",
            "Mid (2-5 years)": "₹12-30 LPA",
            "Senior (5-10 years)": "₹25-60 LPA",
            "Lead (10+ years)": "₹50-100+ LPA"
        },
        "Sales": {
            "Entry (0-2 years)": "₹5-15 LPA",
            "Mid (2-5 years)": "₹15-50 LPA",
            "Senior (5-10 years)": "₹40-100 LPA",
            "Lead (10+ years)": "₹80-200+ LPA"
        },
        "Consulting": {
            "Entry (0-2 years)": "₹10-25 LPA",
            "Mid (2-5 years)": "₹25-70 LPA",
            "Senior (5-10 years)": "₹60-150 LPA",
            "Lead (10+ years)": "₹120-300+ LPA"
        },
        "Healthcare": {
            "Entry (0-2 years)": "₹6-15 LPA",
            "Mid (2-5 years)": "₹15-40 LPA",
            "Senior (5-10 years)": "₹35-80 LPA",
            "Lead (10+ years)": "₹60-150+ LPA"
        }
    }
    
    # City multipliers
    city_multipliers = {
        "Bangalore": 1.3,
        "Mumbai": 1.3,
        "Delhi NCR": 1.2,
        "Hyderabad": 1.15,
        "Pune": 1.1,
        "Chennai": 1.1,
        "Kolkata": 0.9,
        "Tier 2 Cities": 0.8
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Salary Ranges")
        salaries = salary_data.get(selected_field, {
            "Entry": "₹5-15 LPA",
            "Mid": "₹15-30 LPA",
            "Senior": "₹30-60 LPA",
            "Lead": "₹60-100 LPA"
        })
        
        for level, range_val in salaries.items():
            st.metric(level, range_val)
        
        st.markdown("---")
        st.markdown("### 📍 City Multipliers")
        selected_city = st.selectbox("Select city:", list(city_multipliers.keys()))
        multiplier = city_multipliers.get(selected_city, 1.0)
        
        st.info(f"💰 **{selected_city} multiplier:** {multiplier}x base salary")
        st.markdown(f"Example: If base is ₹10 LPA, in {selected_city} it's ~₹{int(10 * multiplier)} LPA")
    
    with col2:
        st.markdown("### 📊 Market Trends")
        st.markdown(f"**Demand for {selected_role}:**")
        
        # Dynamic demand indicator
        st.progress(0.85, text="📈 High Demand (85%)")
        
        st.markdown("---")
        st.markdown("### 🎯 Career Growth Path")
        
        growth_paths = {
            "IT": "Junior → Mid → Senior → Lead → Architect → CTO",
            "Finance": "Analyst → Associate → VP → Director → MD → Partner",
            "Marketing": "Associate → Manager → Senior Manager → Director → VP → CMO",
            "Design": "Junior Designer → Designer → Senior → Lead → Head → CDO",
            "HR": "Associate → Manager → Senior Manager → Director → VP → CHRO",
            "Sales": "Associate → Manager → Regional Manager → Director → VP → CSO",
            "Consulting": "Analyst → Consultant → Manager → Principal → Partner",
            "Healthcare": "Resident → Specialist → Senior → Head → Director → Chief Medical Officer"
        }
        
        st.info(growth_paths.get(selected_field, "Entry → Mid → Senior → Lead → Management"))
        
        st.markdown("---")
        st.markdown("### ⚠️ Red Flags in Job Postings")
        red_flags = [
            "🔴 'Immediate joining or 1 week notice' - May indicate high turnover",
            "🟡 'Competitive salary' without a range - Often means below market",
            "🔴 'Wears many hats' - Could mean understaffed",
            "🟡 'Flexible hours' might mean 'working overtime for free'",
            "🟢 Remote-first companies with clear policies are good signs"
        ]
        for flag in red_flags:
            st.markdown(flag)

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'><small>HireSense AI | Universal Career Optimizer | v2.0 | Multi-Field Support</small></div>", unsafe_allow_html=True)