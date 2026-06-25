import streamlit as st
import requests
import os

# 🎨 Page config
st.set_page_config(
    page_title="HireSense AI - Job Matcher",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Custom CSS
st.markdown("""
    <style>
    .main { padding: 2rem; }
    h1 { color: #667eea; }
    </style>
""", unsafe_allow_html=True)

# 🔥 API URL
API_URL = os.getenv("API_URL", "https://hiresense-api.onrender.com/analyze")
# Header
st.title("🚀 HireSense AI")
st.subheader("Smart Job-Resume Matcher for Indian Job Seekers")

# Sidebar
with st.sidebar:
    st.markdown("### 📋 How It Works:")
    st.markdown("""
    1. Paste your **resume** text
    2. Paste the **job description**
    3. Click **Analyze**
    4. Get detailed match insights!
    """)
    st.divider()
    st.markdown("**Pro Tips:**")
    st.markdown("✅ Copy-paste from PDF or DOCX")
    st.markdown("✅ Include all skills & experience")
    st.markdown("✅ Use complete job descriptions")

# Main content
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Your Resume")
    resume = st.text_area(
        "Paste your resume here:",
        height=300,
        placeholder="Paste your resume text here..."
    )

with col2:
    st.markdown("### 💼 Job Description")
    job_description = st.text_area(
        "Paste the job description here:",
        height=300,
        placeholder="Paste the job description here..."
    )

# Analyze button
if st.button("🔍 Analyze Match", use_container_width=True):
    if not resume or not job_description:
        st.warning("⚠️ Please fill both resume and job description fields")
    else:
        with st.spinner("🤖 Analyzing... This takes a few seconds..."):
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
                    st.divider()

                    # Match Score Display
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        score = data['match_score_percent']
                        if score >= 80:
                            color = "🟢"
                        elif score >= 60:
                            color = "🟡"
                        else:
                            color = "🔴"
                        st.metric(f"{color} Overall Match", f"{score}%")

                    with col2:
                        st.metric("📚 Skills Matched", f"{len(data['matched_skills'])}/{data['total_jd_skills']}")

                    with col3:
                        st.metric("❌ Skills Missing", len(data['missing_skills']))

                    st.divider()

                    # Detailed Analysis
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("### ✅ Matched Skills")
                        if data['matched_skills']:
                            for skill in data['matched_skills']:
                                st.success(f"• {skill}")
                        else:
                            st.info("No skills matched")

                    with col2:
                        st.markdown("### ❌ Missing Skills")
                        if data['missing_skills']:
                            for skill in data['missing_skills']:
                                st.error(f"• {skill}")
                        else:
                            st.success("All required skills present!")

                    st.divider()

                    # Bonus Skills
                    if data['bonus_skills']:
                        st.markdown("### 💪 Bonus Skills (Extra)")
                        for skill in data['bonus_skills'][:5]:
                            st.info(f"**{skill}**")

                    st.divider()

                    # Suggestions
                    st.markdown("### 💡 Suggestions to Improve Match")
                    for i, suggestion in enumerate(data['suggestions'], 1):
                        st.info(f"{i}. {suggestion}")

                    # Download insights
                    st.divider()
                    insights_text = f"""HireSense AI - Match Analysis Report
=====================================

Overall Match Score: {data['match_score_percent']}%
Skill Match Score: {data['skill_match_score']}%
Semantic Similarity: {data['semantic_score']}%

Matched Skills ({len(data['matched_skills'])}): {', '.join(data['matched_skills'])}
Missing Skills ({len(data['missing_skills'])}): {', '.join(data['missing_skills'])}
Bonus Skills ({len(data['bonus_skills'])}): {', '.join(data['bonus_skills'])}

Suggestions:
{chr(10).join([f"- {s}" for s in data['suggestions']])}
"""
                    
                    st.download_button(
                        label="📥 Download Analysis",
                        data=insights_text,
                        file_name="hiresense_analysis.txt",
                        mime="text/plain"
                    )

                else:
                    st.error(f"❌ API Error: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure backend is running on http://127.0.0.1:8000")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: gray;'>
    <small>HireSense AI | Making Job Matching Smarter for Indian Job Seekers</small>
    </div>
""", unsafe_allow_html=True)