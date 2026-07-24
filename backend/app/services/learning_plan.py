from typing import List, Dict
from app.database import db, employees_col

resources_col = db["learning_resources"]


def find_gap_skills(required_skills: List[str], shadow_squad: List[dict]) -> List[str]:
    """Skills required by the project that the shadow squad doesn't cover well."""
    covered = set()
    for member in shadow_squad:
        covered |= set(member["matched_skills"])
    return [s for s in required_skills if s not in covered]


def suggest_mentor_for_skill(skill: str, exclude_ids: List[str]) -> str | None:
    """Find the employee org-wide with the highest confidence score in `skill`."""
    best_name, best_score = None, 0
    for emp in employees_col.find({}):
        if str(emp["_id"]) in exclude_ids:
            continue
        for s in emp.get("skills", []):
            if s["skill"] == skill and s["confidence_score"] > best_score:
                best_score = s["confidence_score"]
                best_name = emp["name"]
    return best_name if best_score >= 50 else None


def generate_bridge_learning_plan(required_skills: List[str], shadow_squad: List[dict]) -> List[Dict]:
    gaps = find_gap_skills(required_skills, shadow_squad)
    squad_ids = [m["employee_id"] for m in shadow_squad]

    plan = []
    for skill in gaps:
        resources = list(resources_col.find({"skill": skill}, {"_id": 0}))
        if not resources:
            resources = [{
                "title": f"Search: '{skill} fundamentals' on Coursera/Pluralsight",
                "url": f"https://www.coursera.org/search?query={skill.replace(' ', '%20')}",
            }]
        plan.append({
            "skill": skill,
            "resources": resources,
            "suggested_mentor": suggest_mentor_for_skill(skill, squad_ids),
        })
    return plan
