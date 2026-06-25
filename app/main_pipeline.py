from app.services.skill_extractor import extract_skills


def run_pipeline(resume: str, job_description: str) -> dict:
    """
    HireSense matching pipeline - simplified for Render deployment.
    Option B: Job Matcher
    """

    # Step 1: Extract skills
    resume_skills = set(extract_skills(resume))
    jd_skills = set(extract_skills(job_description))

    # Step 2: Compute match sets
    matched_skills = sorted(resume_skills & jd_skills)
    missing_skills = sorted(jd_skills - resume_skills)
    bonus_skills = sorted(resume_skills - jd_skills)

    # Step 3: Skill-based score only (simple percentage)
    if jd_skills:
        skill_score = len(matched_skills) / len(jd_skills)
    else:
        skill_score = 0.0

    match_score = round(skill_score * 100, 2)

    # Step 4: Generate suggestions
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
        "semantic_score": 0.0
    }