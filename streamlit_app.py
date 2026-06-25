import streamlit as st
import requests
import os
from app.services.resume_parser import parse_resume

st.set_page_config(
    page_title="HireSense AI - Job Matcher",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Main styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    /* Metrics styling */
    [data-testid="metric-container"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
    }
    
    /* Error messages */
    .stError {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px 30px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Title styling */
    h1 {
        color: #667eea;
        text-align: center;
        margin-bottom: 10px;
    }
    
    h2 {
        color: #764ba2;
        border-bottom: 2px solid #667eea;
        padding-bottom: 10px;
    }
    
    h3 {
        color: #667eea;
    }
    
    /* Skill badge styling */
    .skill-badge {
        display: inline-block;
        background-color: #667eea;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 5px 5px 5px 0;
        font-weight: bold;
    }
    
    /* Container styling */
    .stContainer {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Divider */
    hr {
        border: 2px solid #667eea;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 HireSense AI")
st.subheader("Smart Job-Resume Matcher for Indian Job Seekers")

API_URL = "https://hiresense-ai-3k4d.onrender.com/analyze"

# Sidebar
with st.sidebar:
    st.markdown("### 📋 How It Works:")
    st.markdown("""
    1. **Upload or Paste** your resume
    2. **Upload or Paste** job description
    3. Click **Analyze**
    4. Get detailed insights!
    """)
    st.divider()
    st.markdown("**Supported Formats:**")
    st.markdown("✅ Text (copy-paste)  \n✅ PDF  \n✅ DOCX (Word)")
    st.divider()
    st.markdown("**Pro Tips:**")
    st.markdown("💡 Include all skills & experience  \n💡 Use complete job descriptions  \n💡 Better matching = Better insights")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Single Analyzer", "🔄 Compare Jobs", "🏢 Companies", "ℹ️ About"])

# ============================================================================
# TAB 1: SINGLE ANALYZER
# ============================================================================
with tab1:
    st.markdown("---")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 Your Resume")
        resume_source = st.radio("Resume input method:", ["📝 Paste Text", "📤 Upload File"], key="resume_input")
        
        resume = ""
        if resume_source == "📝 Paste Text":
            resume = st.text_area(
                "Paste your resume here:",
                height=300,
                placeholder="Paste your resume text...",
                key="resume_text"
            )
        else:
            resume_file = st.file_uploader(
                "Upload your resume (PDF or DOCX):",
                type=["pdf", "docx", "doc"],
                key="resume_file"
            )
            if resume_file:
                file_bytes = resume_file.read()
                file_type = resume_file.name.split(".")[-1]
                resume = parse_resume(file_bytes, file_type)
                if resume:
                    st.success(f"✅ Uploaded: {resume_file.name}")
                    st.text_area("Extracted resume text:", value=resume, height=150, disabled=True)
                else:
                    st.error("❌ Could not extract text from file")

    with col2:
        st.markdown("### 💼 Job Description")
        jd_source = st.radio("Job description input method:", ["📝 Paste Text", "📤 Upload File"], key="jd_input")
        
        job_description = ""
        if jd_source == "📝 Paste Text":
            job_description = st.text_area(
                "Paste job description here:",
                height=300,
                placeholder="Paste the job description...",
                key="jd_text"
            )
        else:
            jd_file = st.file_uploader(
                "Upload job description (PDF or DOCX):",
                type=["pdf", "docx", "doc"],
                key="jd_file"
            )
            if jd_file:
                file_bytes = jd_file.read()
                file_type = jd_file.name.split(".")[-1]
                job_description = parse_resume(file_bytes, file_type)
                if job_description:
                    st.success(f"✅ Uploaded: {jd_file.name}")
                    st.text_area("Extracted job description:", value=job_description, height=150, disabled=True)
                else:
                    st.error("❌ Could not extract text from file")

    st.markdown("---")

    # Analyze button
    if st.button("🔍 Analyze Match", use_container_width=True, key="analyze_btn"):
        if not resume or not job_description:
            st.warning("⚠️ Please provide both resume and job description")
        else:
            with st.spinner("🤖 Analyzing your resume..."):
                try:
                    response = requests.post(
                        API_URL,
                        json={
                            "resume": resume,
                            "job_description": job_description
                        },
                        timeout=30
                    )

                    if response.status_code == 200:
                        data = response.json()

                        st.success("✅ Analysis Complete!")
                        st.markdown("---")

                        # Score Display with Progress
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            score = data['match_score_percent']
                            if score >= 80:
                                color = "🟢"
                                sentiment = "Excellent"
                            elif score >= 60:
                                color = "🟡"
                                sentiment = "Good"
                            elif score >= 40:
                                color = "🟠"
                                sentiment = "Fair"
                            else:
                                color = "🔴"
                                sentiment = "Low"
                            
                            st.metric(f"{color} Overall Match", f"{score}%")
                            st.progress(score / 100, text=sentiment)

                        with col2:
                            matched = len(data['matched_skills'])
                            total = data['total_jd_skills']
                            st.metric("✅ Skills Matched", f"{matched}/{total}")
                            st.progress(matched / max(total, 1))

                        with col3:
                            missing = len(data['missing_skills'])
                            st.metric("❌ Skills Missing", missing)
                            if missing == 0:
                                st.success("Perfect! No missing skills")
                            else:
                                st.warning(f"Learn {missing} more skill(s)")

                        st.markdown("---")

                        # Detailed Analysis - Improved
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("### ✅ Matched Skills")
                            if data['matched_skills']:
                                skill_text = " • ".join(data['matched_skills'])
                                st.markdown(f"""
<div style='background-color: #d4edda; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745;'>
<b>🎯 {len(data['matched_skills'])} Skills Found:</b><br>
{skill_text}
</div>
""", unsafe_allow_html=True)
                            else:
                                st.info("No skills matched yet")

                        with col2:
                            st.markdown("### ❌ Missing Skills")
                            if data['missing_skills']:
                                skill_text = " • ".join(data['missing_skills'])
                                st.markdown(f"""
<div style='background-color: #f8d7da; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545;'>
<b>📚 {len(data['missing_skills'])} Skills to Learn:</b><br>
{skill_text}
</div>
""", unsafe_allow_html=True)
                            else:
                                st.success("✨ All required skills present!")

                        st.markdown("---")

                        # Bonus Skills
                        if data['bonus_skills']:
                            st.markdown("### 💪 Bonus Skills (Extra)")
                            bonus_cols = st.columns(min(5, len(data['bonus_skills'])))
                            for i, skill in enumerate(data['bonus_skills'][:5]):
                                with bonus_cols[i % 5]:
                                    st.info(f"🎯 **{skill}**")

                        st.markdown("---")

                        # Suggestions
                        st.markdown("### 💡 Improvement Suggestions")
                        for i, suggestion in enumerate(data['suggestions'], 1):
                            st.info(f"{i}. {suggestion}")

                        st.markdown("---")

                        # Learning Resources
                        if data['missing_skills']:
                            st.markdown("### 📚 Learning Resources")
                            st.markdown("Here are some recommended resources to learn the missing skills:")
                            
                            try:
                                from app.services.learning_service import get_learning_path
                                learning_path = get_learning_path(data['missing_skills'])
                                
                                for learning in learning_path:
                                    with st.expander(f"📖 Learn **{learning['skill'].upper()}** ({learning['difficulty']})"):
                                        resources = learning.get('resources', [])
                                        
                                        if resources:
                                            for i, res in enumerate(resources, 1):
                                                st.markdown(f"""
**{i}. {res.get('name', 'Course')}**
- Type: {res.get('type', 'N/A')}
- Platform: {res.get('platform', 'N/A')}
- Duration: {res.get('duration', 'Self-paced')}
- Rating: {res.get('rating', 'N/A')}
- [Visit Course]({res.get('url', '#')})
""")
                                        else:
                                            st.info(f"No specific resources found for {learning['skill']}")
                            except Exception as e:
                                st.info("Learning resources not available at the moment")

                        st.markdown("---")

                        # Download Results
                        insights_text = f"""HireSense AI - Match Analysis Report
=====================================

Overall Match Score: {data['match_score_percent']}%
Skill Match Score: {data['skill_match_score']}%

Matched Skills ({len(data['matched_skills'])}): {', '.join(data['matched_skills'])}
Missing Skills ({len(data['missing_skills'])}): {', '.join(data['missing_skills'])}
Bonus Skills ({len(data['bonus_skills'])}): {', '.join(data['bonus_skills'])}

SUGGESTIONS:
{chr(10).join([f"{i}. {s}" for i, s in enumerate(data['suggestions'], 1)])}

Generated by HireSense AI
https://hiresense-ai-vishal.streamlit.app
"""
                        
                        st.download_button(
                            label="📥 Download Analysis",
                            data=insights_text,
                            file_name="hiresense_analysis.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                    else:
                        st.error(f"❌ API Error: {response.status_code}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend. Please try again in a moment.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: COMPARE JOBS
# ============================================================================
with tab2:
    st.markdown("### 🔄 Compare Your Resume Against Multiple Jobs")
    st.markdown("Upload or paste your resume once, then compare it against 2-5 different job descriptions to find the best fit!")
    
    st.markdown("---")
    
    # Resume input
    st.markdown("#### 📄 Your Resume")
    compare_resume_source = st.radio(
        "Resume input method:",
        ["📝 Paste Text", "📤 Upload File"],
        key="compare_resume_input"
    )
    
    compare_resume = ""
    if compare_resume_source == "📝 Paste Text":
        compare_resume = st.text_area(
            "Paste your resume here:",
            height=200,
            placeholder="Paste your resume text...",
            key="compare_resume_text"
        )
    else:
        compare_resume_file = st.file_uploader(
            "Upload your resume (PDF or DOCX):",
            type=["pdf", "docx", "doc"],
            key="compare_resume_file"
        )
        if compare_resume_file:
            file_bytes = compare_resume_file.read()
            file_type = compare_resume_file.name.split(".")[-1]
            compare_resume = parse_resume(file_bytes, file_type)
            if compare_resume:
                st.success(f"✅ Uploaded: {compare_resume_file.name}")
            else:
                st.error("❌ Could not extract text")
    
    st.markdown("---")
    
    # Job descriptions
    st.markdown("#### 💼 Job Descriptions (2-5 jobs)")
    num_jobs = st.slider("How many jobs to compare?", min_value=2, max_value=5, value=2)
    
    job_descriptions = []
    for i in range(num_jobs):
        st.markdown(f"**Job {i+1}:**")
        job_col1, job_col2 = st.columns(2)
        
        with job_col1:
            job_source = st.radio(
                "Input method:",
                ["📝 Paste", "📤 Upload"],
                key=f"job_source_{i}",
                horizontal=True
            )
        
        with job_col2:
            pass
        
        if job_source == "📝 Paste":
            job_text = st.text_area(
                f"Paste job {i+1} description:",
                height=150,
                placeholder="Paste job description...",
                key=f"job_text_{i}"
            )
            job_descriptions.append(job_text)
        else:
            job_file = st.file_uploader(
                f"Upload job {i+1} description:",
                type=["pdf", "docx", "doc", "txt"],
                key=f"job_file_{i}"
            )
            if job_file:
                file_bytes = job_file.read()
                file_type = job_file.name.split(".")[-1]
                job_text = parse_resume(file_bytes, file_type)
                job_descriptions.append(job_text)
            else:
                job_descriptions.append("")
        
        st.divider()
    
    # Compare button
    if st.button("🔍 Compare Resume Against All Jobs", use_container_width=True, key="compare_btn"):
        if not compare_resume or not any(job_descriptions):
            st.warning("⚠️ Please provide resume and at least one job description")
        else:
            with st.spinner("📊 Comparing your resume..."):
                try:
                    response = requests.post(
                        API_URL.replace("/analyze", "/compare"),
                        json={
                            "resume": compare_resume,
                            "jobs": [j for j in job_descriptions if j.strip()]
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        st.success("✅ Comparison Complete!")
                        st.markdown("---")
                        
                        # Summary metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "🏆 Best Match",
                                f"Job {data['best_match_job']}",
                                f"{data['best_match_score']}%"
                            )
                        
                        with col2:
                            st.metric(
                                "📊 Average Match",
                                f"{data['average_score']}%",
                                f"Across {data['total_jobs']} jobs"
                            )
                        
                        with col3:
                            st.metric(
                                "⚠️ Worst Match",
                                f"Job {data['worst_match_job']}",
                                f"{data['worst_match_score']}%"
                            )
                        
                        st.markdown("---")
                        
                        # Detailed comparison
                        st.markdown("### 📈 Detailed Comparison")
                        
                        # Create comparison table
                        comparison_data = []
                        for result in data['results']:
                            comparison_data.append({
                                "Job": f"Job {result['job_number']}",
                                "Match %": result['match_score_percent'],
                                "Matched Skills": len(result['matched_skills']),
                                "Missing Skills": len(result['missing_skills'])
                            })
                        
                        st.dataframe(comparison_data, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # Detailed results for each job
                        st.markdown("### 📋 Job-by-Job Breakdown")
                        
                        for i, result in enumerate(data['results'], 1):
                            with st.expander(f"Job {i} Details (Match: {result['match_score_percent']}%)", 
                                           expanded=(i == data['best_match_job'])):
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**✅ Matched Skills:**")
                                    if result['matched_skills']:
                                        st.markdown(", ".join(result['matched_skills']))
                                    else:
                                        st.info("No matched skills")
                                
                                with col2:
                                    st.markdown("**❌ Missing Skills:**")
                                    if result['missing_skills']:
                                        st.markdown(", ".join(result['missing_skills']))
                                    else:
                                        st.success("All skills present!")
                                
                                st.markdown("**💡 Suggestions:**")
                                for suggestion in result['suggestions']:
                                    st.info(suggestion)
                        
                        st.markdown("---")
                        
                        # Recommendation
                        best_job = data['best_match_job']
                        best_score = data['best_match_score']
                        
                        st.markdown("### 🎯 Recommendation")
                        st.markdown(f"Based on your resume, **Job {best_job}** is the best fit with a match score of **{best_score}%**. This job aligns well with your skills and experience. Focus on learning the missing skills and you will be a strong candidate!")
                    
                    else:
                        st.error(f"❌ API Error: {response.status_code}")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 3: COMPANY DATABASE
# ============================================================================
with tab3:
    st.markdown("### 🏢 Company Database & Insights")
    st.markdown("Explore top companies, their tech stack, interview process, and salary ranges")
    
    st.markdown("---")
    
    # Industry selector
    try:
        from app.services.company_service import get_industries, get_companies_by_industry, get_company_insights
        
        industries = get_industries()
        industry_names = [ind["name"] for ind in industries]
        industry_keys = [ind["key"] for ind in industries]
        
        selected_industry_name = st.selectbox(
            "Select Industry:",
            industry_names,
            key="industry_select"
        )
        
        selected_industry_key = industry_keys[industry_names.index(selected_industry_name)]
        
        st.markdown("---")
        
        # Show industry insights
        insights = get_company_insights(selected_industry_key)
        
        if insights:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Total Companies", insights.get("total_companies", 0))
            
            with col2:
                st.metric("💰 Avg Salary Range", insights.get("average_salary", "N/A"))
            
            with col3:
                st.metric("🔧 Common Tech Skills", len(insights.get("common_tech_stack", [])))
        
        st.markdown("---")
        
        # Get companies
        industry_data = get_companies_by_industry(selected_industry_key)
        companies = industry_data.get("companies", [])
        
        st.markdown(f"### Companies in {selected_industry_name}")
        
        for company in companies:
            with st.expander(f"🏢 **{company.get('name')}** | {company.get('salary_range')}"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Type:** {company.get('type', 'N/A')}")
                    st.markdown(f"**HQ:** {company.get('headquarters', 'N/A')}")
                    st.markdown(f"**Founded:** {company.get('founded', 'N/A')}")
                    st.markdown(f"**Difficulty:** {company.get('difficulty', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Salary Range:** {company.get('salary_range', 'N/A')}")
                    st.markdown(f"**Tech Stack:** {', '.join(company.get('tech_stack', []))}")
                
                st.markdown("**Hiring Roles:**")
                st.markdown(", ".join(company.get("hiring_roles", [])))
                
                st.markdown("**Interview Process:**")
                st.info(company.get("interview_process", "N/A"))
                
                st.markdown("**Popular Interview Questions:**")
                for q in company.get("popular_questions", []):
                    st.markdown(f"- {q}")
    
    except Exception as e:
        st.error(f"Error loading company database: {str(e)}")

# ============================================================================
# TAB 4: ABOUT
# ============================================================================
with tab4:
    st.markdown("""
## About HireSense AI

HireSense AI is your personal job-matching assistant, designed for job seekers worldwide.

### 🎯 Our Mission
Help job seekers make data-driven career decisions by providing instant insights into resume-job alignment.

### ✨ What Makes Us Different
- **Smart Skill Matching:** Recognizes skill variations (REST APIs = REST API)
- **Multi-Industry:** Supports IT, Finance, Marketing, Design, HR, and more
- **Free & Anonymous:** No signups, no tracking
- **Instant Results:** Get insights in seconds
- **Compare Jobs:** Find the best fit among multiple opportunities
- **Company Insights:** Explore top companies and interview processes
- **Learning Resources:** Get recommended courses for missing skills

### 🔧 Technology
- **Backend:** FastAPI + Python
- **Frontend:** Streamlit
- **Deployment:** Render + Streamlit Cloud
- **Skill Database:** 40+ common tech skills
- **Company Database:** 30+ top companies across 5 industries

### 📊 How Matching Works
1. **Skill Extraction:** Identifies technical skills from text
2. **Normalization:** Handles variations (microservices = microservice)
3. **Matching:** Compares resume skills with job requirements
4. **Scoring:** Calculates match percentage
5. **Suggestions:** Recommends improvements

### 🚀 Live Demo
**App:** https://hiresense-ai-vishal.streamlit.app  
**GitHub:** https://github.com/lonewolf1621/hiresense-ai  
**API:** https://hiresense-ai-3k4d.onrender.com

### 💬 Feedback
Found a bug? Have a suggestion? Create an issue on GitHub!

---

**Made with ❤️ for Job Seekers Worldwide**
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
<small>HireSense AI | Smart Resume-Job Matching | v1.3 | Multi-Industry Support Now Available!</small>
</div>
""", unsafe_allow_html=True)