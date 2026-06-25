from app.services.skill_extractor import extract_skills
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

# Load model once
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print(f"Warning: Could not load sentence transformer: {e}")
    model = None


def run_pipeline(resume: str, job_description: str) -> dict:
    """
    Enhanced HireSense matching pipeline with semantic similarity.
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

    # Step 4: Semantic similarity score
    semantic_score = 0.0
    try:
        if model:
            resume_vec = model.encode(resume)
            jd_vec = model.encode(job_description)
            semantic_score = float(cosine_similarity([resume_vec], [jd_vec])[0][0])
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