import re

# 🔥 Core technical skills
SKILLS_DB = [
    "python", "tensorflow", "pytorch", "nlp",
    "machine learning", "deep learning",
    "docker", "kubernetes", "sql", "pandas",
    "fastapi", "api", "microservices", "rest",
    "linux", "git", "mlops", "ci/cd"
]

# 🔥 Role-based inferred skills (NEW)
ROLE_KEYWORDS = {
    "software engineer": ["python", "api", "git"],
    "backend": ["api", "fastapi", "sql"],
    "ml engineer": ["machine learning", "python"],
    "data": ["sql", "pandas"],
}


def extract_skills(text):
    text = text.lower()

    found_skills = set()

    # 🔥 1. Direct keyword match
    for skill in SKILLS_DB:
        if re.search(r"\b" + re.escape(skill) + r"\b", text):
            found_skills.add(skill)

    # 🔥 2. Role-based inference (IMPORTANT FIX)
    for role, skills in ROLE_KEYWORDS.items():
        if role in text:
            for s in skills:
                found_skills.add(s)

    # 🔥 3. Fallback (CRITICAL)
    if not found_skills:
        # Basic fallback extraction
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
        found_skills.update(words[:5])  # take first few meaningful words

    return list(found_skills)