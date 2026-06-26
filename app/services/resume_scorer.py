import json
import os
import re
from collections import Counter

def load_field_data():
    """Load field and role data"""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "fields_roles.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {"fields": [], "field_keywords": {}}


def score_resume(resume_text, field, role):
    """
    Score resume based on field and role.
    Returns score (0-100) with detailed breakdown.
    """
    
    field_data = load_field_data()
    field_keywords = field_data.get("field_keywords", {}).get(field, {})
    
    score = 0
    issues = []
    improvements = []
    strengths = []
    
    resume_lower = resume_text.lower()
    resume_words = resume_lower.split()
    
    # 1. LENGTH CHECK (10 points)
    word_count = len(resume_words)
    if 300 <= word_count <= 800:
        score += 10
        strengths.append("✅ Resume length is optimal (300-800 words)")
    elif word_count < 300:
        issues.append("Resume too short (< 300 words)")
        improvements.append("📝 Expand your resume to include more achievements and details")
        score += 5
    else:
        issues.append("Resume too long (> 800 words)")
        improvements.append("✂️ Trim your resume to fit on 1 page, focus on recent achievements")
    
    # 2. CONTACT INFORMATION (5 points)
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\+?91?\s?[6-9]\d{9}'
    
    if re.search(email_pattern, resume_text):
        score += 3
        strengths.append("✅ Email address found")
    else:
        issues.append("Missing email address")
        improvements.append("📧 Add your email address at the top")
    
    if re.search(phone_pattern, resume_text):
        score += 2
        strengths.append("✅ Phone number found")
    else:
        issues.append("Missing phone number")
        improvements.append("📱 Add your phone number")
    
    # 3. FIELD-SPECIFIC SKILLS (30 points)
    skills = field_keywords.get("skills", [])
    found_skills = []
    
    for skill in skills:
        if skill.lower() in resume_lower:
            found_skills.append(skill)
    
    if found_skills:
        skill_percentage = (len(found_skills) / len(skills)) * 30 if skills else 0
        score += min(skill_percentage, 30)
        strengths.append(f"✅ Found {len(found_skills)} key skills: {', '.join(found_skills)}")
    else:
        issues.append(f"Missing key {field} skills")
        missing = skills[:3]
        improvements.append(f"🎯 Add key {field} skills: {', '.join(missing)}")
    
    if len(found_skills) < len(skills) / 2:
        missing_skills = [s for s in skills if s.lower() not in resume_lower]
        improvements.append(f"📚 Consider adding these skills: {', '.join(missing_skills[:3])}")
    
    # 4. ACTION VERBS (10 points)
    action_verbs = [
        "led", "managed", "developed", "created", "designed", "implemented",
        "achieved", "improved", "increased", "built", "launched", "optimized",
        "drove", "transformed", "delivered", "analyzed", "engineered"
    ]
    
    action_count = sum(1 for verb in action_verbs if verb in resume_lower)
    if action_count > 5:
        score += 10
        strengths.append(f"✅ Strong action verbs used ({action_count} found)")
    elif action_count > 0:
        score += 5
        improvements.append(f"💪 Use more action verbs (found {action_count}, aim for 5+)")
    else:
        issues.append("Weak language in resume")
        improvements.append("💪 Replace passive language with action verbs: Led, Built, Achieved, etc.")
    
    # 5. QUANTIFIABLE ACHIEVEMENTS (15 points)
    numbers_pattern = r'\d+[%+x]?'
    numbers = re.findall(numbers_pattern, resume_lower)
    
    if len(numbers) > 5:
        score += 15
        strengths.append(f"✅ Strong use of metrics and numbers ({len(numbers)} found)")
    elif len(numbers) > 0:
        score += 8
        improvements.append(f"📊 Add more quantifiable achievements (numbers, %, metrics)")
    else:
        issues.append("Lacks quantifiable results")
        improvements.append("📊 Add numbers: 'Increased sales by 35%', 'Reduced costs by $50K', etc.")
    
    # 6. KEYWORDS/JARGON (15 points)
    keywords = field_keywords.get("keywords", [])
    found_keywords = []
    
    for keyword in keywords:
        if keyword.lower() in resume_lower:
            found_keywords.append(keyword)
    
    if found_keywords:
        keyword_percentage = (len(found_keywords) / len(keywords)) * 15 if keywords else 0
        score += min(keyword_percentage, 15)
        strengths.append(f"✅ Industry keywords: {', '.join(found_keywords)}")
    else:
        improvements.append(f"🏷️ Add industry keywords: {', '.join(keywords[:3])}")
    
    # 7. CERTIFICATIONS (10 points)
    certs = field_keywords.get("certifications", [])
    found_certs = []
    
    for cert in certs:
        if cert.lower() in resume_lower:
            found_certs.append(cert)
    
    if found_certs:
        score += min((len(found_certs) / len(certs)) * 10, 10) if certs else 0
        strengths.append(f"✅ Relevant certifications: {', '.join(found_certs)}")
    else:
        improvements.append(f"🎓 Consider adding certifications: {', '.join(certs[:2])}")
    
    # 8. FORMATTING (5 points)
    if len(resume_text.split('\n')) > 3:  # Has line breaks
        score += 3
    
    if resume_text.count('•') > 3 or resume_text.count('-') > 3:  # Has bullets
        score += 2
        strengths.append("✅ Good formatting with bullet points")
    else:
        improvements.append("📋 Use bullet points for better readability")
    
    # Final score
    final_score = min(score, 100)
    
    return {
        "score": round(final_score, 1),
        "field": field,
        "role": role,
        "strengths": strengths,
        "issues": issues,
        "improvements": improvements,
        "matched_skills": found_skills,
        "matched_keywords": found_keywords,
        "matched_certifications": found_certs,
        "word_count": word_count,
        "action_verb_count": action_count,
        "metric_count": len(numbers),
        "ats_score": round((final_score / 100) * 100, 1),
        "recommendations": improvements
    }


def suggest_improvements(resume_text, field, role):
    """Generate specific improvement suggestions"""
    field_data = load_field_data()
    field_keywords = field_data.get("field_keywords", {}).get(field, {})
    
    suggestions = []
    
    # 1. Missing skills
    skills = field_keywords.get("skills", [])
    resume_lower = resume_text.lower()
    missing_skills = [s for s in skills if s.lower() not in resume_lower]
    
    if missing_skills:
        suggestions.append({
            "type": "Skills",
            "priority": "High",
            "issue": f"Missing key {field} skills",
            "suggestion": f"Add these skills to your resume: {', '.join(missing_skills[:5])}",
            "impact": "35% better ATS matching"
        })
    
    # 2. Weak bullets
    if resume_text.count('•') < 10:
        suggestions.append({
            "type": "Format",
            "priority": "Medium",
            "issue": "Insufficient bullet points",
            "suggestion": "Use 10-15 bullet points to highlight achievements",
            "impact": "Easier for recruiters to scan"
        })
    
    # 3. No metrics
    if len(re.findall(r'\d+[%+x]?', resume_text.lower())) < 5:
        suggestions.append({
            "type": "Content",
            "priority": "High",
            "issue": "Lacks quantifiable results",
            "suggestion": "Replace vague statements with metrics: 'Increased revenue by 40%', 'Reduced turnaround time by 50%'",
            "impact": "50% more impact"
        })
    
    # 4. Missing certifications
    certs = field_keywords.get("certifications", [])
    if certs:
        suggestions.append({
            "type": "Credentials",
            "priority": "Medium",
            "issue": "No certifications mentioned",
            "suggestion": f"Highlight certifications: {', '.join(certs[:3])}",
            "impact": "Shows commitment to field"
        })
    
    return suggestions