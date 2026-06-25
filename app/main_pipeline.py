from app.services.skill_extractor import extract_skills
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


def run_pipeline(resume: str, job_description: str) -> dict:
    """
    Enhanced HireSense matching pipeline with TF-IDF similarity.
    Option B: Job Matcher
    """

    # Step 1: Extract skills
    resume_skills = set(extract_skills(resume))
    jd_skills = set(extract_skills(job_description))

    # Step 2: Compute match sets
    matched_skills = sorted(resume_skills & jd_skills)
    missing_skills = sorted(jd_skills - resume_skills)
    bonus_skills = sorted(resume_skills - jd_skills)

    # Step 3: Skill-based score
    if jd_skills:
        skill_score = len(matched_skills) / len(jd_skills)
    else:
        skill_score = 0.0

    # Step 4: Semantic similarity score using TF-IDF (lightweight alternative)
    semantic_score = 0.0
    try:
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3))
        vectors = vectorizer.fit_transform([resume, job_description])
        semantic_score = float(cosine_similarity(vectors[0], vectors[1])[0][0])
    except Exception as e:
        print(f"Warning: Semantic scoring failed: {e}")
        semantic_score = 0.0

    # Step 5: Hybrid score (70% skills + 30% semantic)
    match_score = round((0.7 * skill_score + 0.3 * semantic_score) * 100, 2)

    # Step 6: Generate suggestions
    suggestions = []
    
    if missing_skills:
        top_missing = missing_skills[:5]
        suggestions.append(f"📚 Learn these skills: {', '.join(top_missing)}")
    
    if match_score >= 80:
        suggestions.append("✅ Excellent match! You meet most requirements.")
    elif match_score >= 60:
        suggestions.append("⚠️ Good match. Highlight relevant experience better.")
    elif match_score >= 40:
        suggestions.append("🎯 Fair match. Consider upskilling in key areas.")
    else:
        suggestions.append("❌ Low match. Focus on gaining experience in missing skills.")

    if bonus_skills:
        top_bonus = bonus_skills[:3]
        suggestions.append(f"💪 Leverage these extra skills: {', '.join(top_bonus)}")

    return {
        "match_score_percent": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "bonus_skills": bonus_skills,
        "total_jd_skills": len(jd_skills),
        "total_resume_skills": len(resume_skills),
        "suggestions": suggestions,
        "skill_match_score": round(skill_score * 100, 2),
        "semantic_score": round(semantic_score * 100, 2)
    }