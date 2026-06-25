import re
import json
import os

# Load skills database
SKILLS_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skills_db.json")

try:
    with open(SKILLS_DB_PATH, "r") as f:
        SKILLS_DATA = json.load(f)
        SKILLS_DB = SKILLS_DATA.get("core_skills", [])
        ROLE_KEYWORDS = SKILLS_DATA.get("role_keywords", {})
except Exception as e:
    print(f"Warning: Could not load skills_db.json: {e}")
    # Fallback
    SKILLS_DB = [
        "python", "java", "javascript", "react", "angular",
        "fastapi", "django", "node.js", "sql", "mongodb",
        "aws", "docker", "kubernetes", "git", "linux",
        "machine learning", "tensorflow", "pytorch"
    ]
    ROLE_KEYWORDS = {}


def extract_skills(text):
    """Extract technical skills from resume or job description."""
    text = text.lower()
    found_skills = set()

    # 1. Direct keyword match
    for skill in SKILLS_DB:
        if re.search(r"\b" + re.escape(skill) + r"\b", text):
            found_skills.add(skill)

    # 2. Role-based inference
    for role, skills in ROLE_KEYWORDS.items():
        if role in text:
            for s in skills:
                found_skills.add(s)

    # 3. Fallback - extract technical terms
    if not found_skills:
        words = re.findall(r"\b[a-z]{3,}\b", text)
        found_skills.update(words[:10])

    return sorted(list(found_skills))