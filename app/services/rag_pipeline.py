from app.services.skill_extractor import extract_skills
from app.services.embedding import embed_text
from sklearn.metrics.pairwise import cosine_similarity


def run_rag_pipeline(resume_text, jd_text):
    print("🚀 Starting pipeline...")

    # 🔥 Extract skills
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    print("RESUME SKILLS:", resume_skills)
    print("JD SKILLS:", jd_skills)

    # 🔥 Handle empty JD skills
    if not jd_skills:
        return {
            "match_score": 0,
            "resume_skills": resume_skills,
            "jd_skills": jd_skills,
            "missing_skills": [],
            "strengths": [],
            "suggestions": ["Job description skills not detected properly"]
        }

    # 🔥 Embeddings
    resume_vec = embed_text(resume_text)
    jd_vec = embed_text(jd_text)

    similarity = cosine_similarity([resume_vec], [jd_vec])[0][0]

    # 🔥 HYBRID SCORING (FIXED)
    matched = len(set(resume_skills) & set(jd_skills))
    total = len(jd_skills)

    if total == 0:
        skill_score = 0
    else:
        skill_score = matched / total

    match_score = float((0.7 * skill_score + 0.3 * similarity) * 100)

    # 🔥 Missing skills
    missing_skills = list(set(jd_skills) - set(resume_skills))

    # 🔥 Strengths
    strengths = []
    if "python" in resume_skills:
        strengths.append("Strong Python experience")
    if "nlp" in resume_skills:
        strengths.append("Experience in NLP")
    if "docker" in resume_skills:
        strengths.append("Experience with Docker")

    # 🔥 Suggestions
    suggestions = []
    if missing_skills:
        suggestions.append(f"Add missing skills: {', '.join(missing_skills)}")
    suggestions.append("Include measurable achievements")

    print("✅ Pipeline finished")

    # ✅ RETURN MUST BE INSIDE FUNCTION
    return {
        "match_score": match_score,
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "suggestions": suggestions
    }