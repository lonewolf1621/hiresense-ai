import re

# Skill aliases - handle variations
SKILL_ALIASES = {
    "rest": "rest api",
    "rest apis": "rest api",
    "restful": "rest api",
    "restful api": "rest api",
    "api": "rest api",
    "microservices": "microservice",
    "microservice": "microservice",
    "ml": "machine learning",
    "ai": "machine learning",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "nodejs": "node.js",
    "node": "node.js",
    "postgres": "postgresql",
    "mongo": "mongodb",
}

SKILLS_DB = [
    "python", "java", "javascript", "c++", "go", "rust",
    "sql", "mongodb", "postgresql", "mysql", "redis",
    "react", "angular", "vue", "node.js", "django", "fastapi",
    "aws", "azure", "gcp", "docker", "kubernetes",
    "git", "linux", "rest api", "graphql", "microservice",
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "agile", "scrum", "jira", "ci/cd", "jenkins", "gitlab",
    "html", "css", "typescript", "kotlin", "swift",
]

def extract_skills(text):
    """Extract technical skills - pure Python, no dependencies"""
    text = text.lower()
    found_skills = set()

    # 1. Check aliases first (handles variations)
    for alias, canonical in SKILL_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text):
            found_skills.add(canonical)

    # 2. Check core skills
    for skill in SKILLS_DB:
        if re.search(r'\b' + re.escape(skill) + r'\b', text):
            found_skills.add(skill)

    # 3. Fallback
    if not found_skills:
        words = re.findall(r'\b[a-z]{3,}\b', text)
        found_skills.update(words[:10])

    return sorted(list(found_skills))