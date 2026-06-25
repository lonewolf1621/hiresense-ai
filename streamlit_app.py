import streamlit as st
import requests

st.set_page_config(page_title="HireSense AI", layout="wide")

st.title("🚀 HireSense AI")
st.subheader("Resume-Job Matcher")

API_URL = "https://hiresense-ai-3k4d.onrender.com/analyze"

tab1, tab2 = st.tabs(["Analyzer", "About"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        resume = st.text_area("Resume:", height=300)
    
    with col2:
        jd = st.text_area("Job Description:", height=300)
    
    if st.button("Analyze"):
        if resume and jd:
            with st.spinner("Analyzing..."):
                try:
                    r = requests.post(API_URL, json={"resume": resume, "job_description": jd}, timeout=30)
                    if r.status_code == 200:
                        data = r.json()
                        st.success("Done!")
                        
                        c1, c2, c3 = st.columns(3)
                        with c1: st.metric("Match %", f"{data['match_score_percent']}%")
                        with c2: st.metric("Matched", len(data['matched_skills']))
                        with c3: st.metric("Missing", len(data['missing_skills']))
                        
                        st.markdown(f"**Matched:** {', '.join(data['matched_skills'])}")
                        st.markdown(f"**Missing:** {', '.join(data['missing_skills'])}")
                        
                        for s in data['suggestions']:
                            st.info(s)
                    else:
                        st.error(f"API Error")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Fill both fields")

with tab2:
    st.markdown("HireSense AI - Smart matching tool")
    st.markdown("[GitHub](https://github.com/lonewolf1621/hiresense-ai)")