import json
import os


def load_learning_resources():
    """Load learning resources database"""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "learning_resources.json")
    
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {"learning_resources": {}}


def get_learning_resources(skill):
    """Get learning resources for a specific skill"""
    resources = load_learning_resources()
    skill_key = skill.lower().strip()
    
    # Try exact match
    if skill_key in resources["learning_resources"]:
        return resources["learning_resources"][skill_key]
    
    # Try partial match
    for key, value in resources["learning_resources"].items():
        if key in skill_key or skill_key in key:
            return value
    
    # Return default
    return resources["learning_resources"].get("default", {})


def get_learning_path(missing_skills):
    """Generate a learning path for missing skills"""
    learning_path = []
    
    for skill in missing_skills:
        resource = get_learning_resources(skill)
        if resource:
            learning_path.append({
                "skill": skill,
                "difficulty": resource.get("difficulty", "Unknown"),
                "resources": resource.get("resources", [])
            })
    
    return learning_path