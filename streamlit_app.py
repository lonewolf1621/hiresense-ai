import streamlit as st
import requests
import os

# 🔥 API URL
API_URL = os.getenv("API_URL", "http://127.0.0.1:8001/analyze")

st.set_page_config(page_title="HireSense AI", layout="centered")

st.title("🚀 HireSense AI")
st.subheader("AI Resume–Job Matching System")

st.write("Paste your resume and job description below to analyze match.")

# 🔥 Inputs
resume = st.text_area("📄 Resume", height=200)
job_description = st.text_area("💼 Job Description", height=200)

# 🔥 Button
if st.button("Analyze"):
    if not resume or not job_description:
        st.warning("Please fill both fields")
    else:
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "resume": resume,
                        "job_description": job_description
                    }
                )

                if response.status_code == 200:
                    data = response.json()

                    st.success("Analysis Complete ✅")

                    # 🔥 Display results
                    st.subheader("📊 Match Score")
                    st.metric("Score", f"{round(data['match_score'], 2)}")

                    st.subheader("🧠 Skills")
                    st.write("**Resume Skills:**", data["resume_skills"])
                    st.write("**Job Skills:**", data["jd_skills"])
                    st.write("**Missing Skills:**", data["missing_skills"])

                    st.subheader("💪 Strengths")
                    for s in data["strengths"]:
                        st.write(f"- {s}")

                    st.subheader("📈 Suggestions")
                    for s in data["suggestions"]:
                        st.write(f"- {s}")

                else:
                    st.error("API Error")

            except Exception as e:
                st.error(f"Error: {e}")