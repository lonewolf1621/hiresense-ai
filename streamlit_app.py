import streamlit as st
import requests
import os
import tempfile
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
tab1, tab2 = st.tabs(["📊 Analyzer", "ℹ️ About"])

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
                                color_code = "#28a745"
                            elif score >= 60:
                                color = "🟡"
                                sentiment = "Good"
                                color_code = "#ffc107"
                            elif score >= 40:
                                color = "🟠"
                                sentiment = "Fair"
                                color_code = "#fd7e14"
                            else:
                                color = "🔴"
                                sentiment = "Low"
                                color_code = "#dc3545"
                            
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

with tab2:
    st.markdown("""
    ## About HireSense AI
    
    HireSense AI is your personal job-matching assistant, designed specifically for Indian job seekers.
    
    ### 🎯 Our Mission
    Help job seekers make data-driven career decisions by providing instant insights into resume-job alignment.
    
    ### ✨ What Makes Us Different
    - **Smart Skill Matching:** Recognizes skill variations (REST APIs = REST API)
    - **India-Focused:** Understands Indian tech job market
    - **Free & Anonymous:** No signups, no tracking
    - **Instant Results:** Get insights in seconds
    
    ### 🔧 Technology
    - **Backend:** FastAPI + Python
    - **Frontend:** Streamlit
    - **Deployment:** Render + Streamlit Cloud
    - **Skill Database:** 40+ common tech skills
    
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
    
    **Made with ❤️ for Indian Job Seekers**
    """)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray;'>
    <small>HireSense AI | Smart Resume-Job Matching | v1.1</small>
    </div>
""", unsafe_allow_html=True)