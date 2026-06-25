import streamlit as st
import requests
import os

st.set_page_config(
    page_title="HireSense AI - Job Matcher",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 HireSense AI")
st.subheader("Smart Job-Resume Matcher for Indian Job Seekers")

API_URL = "https://hiresense-ai-3k4d.onrender.com/analyze"

with st.sidebar:
    st.markdown("### 📋 How It Works:")
    st.markdown("""
    1. Paste your **resume** text
    2. Paste the **job description**
    3. Click **Analyze**
    4. Get match insights!
    """)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Your Resume")
    resume = st.text_area("Paste your resume here:", height=300)

with col2:
    st.markdown("### 💼 Job Description")
    job_description = st.text_area("Paste job description here:", height=300)

if st.button("🔍 Analyze Match", use_container_width=True):
    if not resume or not job_description:
        st.warning("⚠️ Please fill both fields")
    else:
        with st.spinner("🤖 Analyzing..."):
            try:
                response = requests.post(
                    API_URL,
                    json={"resume": resume, "job_description": job_description},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    st.success("✅ Analysis Complete!")
                    st.divider()

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        score = data['match_score_percent']
                        st.metric("Overall Match", f"{score}%")
                    with col2:
                        st.metric("Skills Matched", f"{len(data['matched_skills'])}/{data['total_jd_skills']}")
                    with col3:
                        st.metric("Skills Missing", len(data['missing_skills']))

                    st.divider()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### ✅ Matched Skills")
                        for skill in data['matched_skills']:
                            st.success(f"• {skill}")

                    with col2:
                        st.markdown("### ❌ Missing Skills")
                        for skill in data['missing_skills']:
                            st.error(f"• {skill}")

                    st.divider()
                    st.markdown("### 💡 Suggestions")
                    for suggestion in data['suggestions']:
                        st.info(suggestion)

                else:
                    st.error(f"API Error: {response.status_code}")

            except Exception as e:
                st.error(f"Error: {str(e)}")

st.divider()
st.markdown("<div style='text-align: center;'><small>HireSense AI | Job Matching Made Smart</small></div>", unsafe_allow_html=True)