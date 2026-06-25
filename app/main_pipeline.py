# app/main_pipeline.py
from app.services.skill_extractor import extract_skills


def run_pipeline(resume: str, job_description: str) -> dict:
    """
    Core HireSense matching pipeline.
    Extracts skills from resume & JD, then computes match analysis.
    """

    # Step 1 — Extract skills from both inputs
    resume_skills = set(extract_skills(resume))
    jd_skills = set(extract_skills(job_description))

    # Step 2 — Compute match sets
    matched_skills  = sorted(resume_skills & jd_skills)
    missing_skills  = sorted(jd_skills - resume_skills)
    bonus_skills    = sorted(resume_skills - jd_skills)

    # Step 3 — Score (avoid division by zero)
    if jd_skills:
        match_score = round(len(matched_skills) / len(jd_skills) * 100, 2)
    else:
        match_score = 0.0

    # Step 4 — Generate actionable suggestions
    suggestions = []
    if missing_skills:
        suggestions.append(
            f"Consider adding these skills to your resume: {', '.join(missing_skills)}"
        )
    if match_score >= 80:
        suggestions.append("Strong match! You meet most of the job requirements.")
    elif match_score >= 50:
        suggestions.append("Moderate match. Highlighting more relevant experience will help.")
    else:
        suggestions.append("Low match. Consider upskilling or tailoring your resume more carefully.")

    return {
        "match_score_percent": match_score,
        "matched_skills":      matched_skills,
        "missing_skills":      missing_skills,
        "bonus_skills":        bonus_skills,
        "total_jd_skills":     len(jd_skills),
        "total_resume_skills": len(resume_skills),
        "suggestions":         suggestions,
    }