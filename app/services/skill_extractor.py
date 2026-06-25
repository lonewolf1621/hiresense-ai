import re
import json
import os

# Load skills database - FIX PATH
def load_skills_db():
    """Load skills database from JSON file"""
    # Try multiple paths
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "data", "skills_db.json"),
        os.path.join(os.getcwd(), "data", "skills_db.json"),
        "data/skills_db.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {path}: {e}")
    
    # Fallback if file not found
    return {
        "core_skills": [
            "python", "java", "javascript", "c++", "go", "rust",
            "sql", "mongodb", "postgresql", "mysql", "redis",
            "react", "angular", "vue", "node.js", "django", "fastapi",
            "aws", "azure", "gcp", "docker", "kubernetes",
            "git", "linux", "rest api", "graphql", "microservices",
            "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
            "agile", "scrum", "jira", "ci/cd", "jenkins", "gitlab"
        ],
        "role_keywords": {
            "backend developer": ["fastapi", "api", "sql", "docker", "python"],
            "frontend developer": ["react", "javascript", "css", "html", "angular"],
            "full stack developer": ["python", "javascript", "react", "sql", "api"],
            "data engineer": ["sql", "python", "spark", "hadoop", "etl"],
            "ml engineer": ["machine learning", "python", "tensorflow", "pytorch"],
            "devops engineer": ["docker", "kubernetes", "jenkins", "aws", "linux"]
        }
    }


SKILLS_DATA = load_skills_db()
SKILLS_DB = SKILLS_DATA.get("core_skills", [])
ROLE_KEYWORDS = SKILLS_DATA.get("role_keywords", {})


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