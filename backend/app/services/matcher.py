"""
Matches employees to a project's required skills, predicts transferable
("adjacent") skills, and forms a Shadow Squad using a greedy set-cover
over the required skills, preferring higher confidence scores.
"""
from typing import List, Dict

# Simple transferable-skill map: if someone is strong in the key skill,
# they can likely ramp up quickly in the associated adjacent skills.
ADJACENCY_MAP = {
    "javascript": ["typescript", "react", "node.js"],
    "react": ["javascript", "typescript", "html/css"],
    "python": ["fastapi", "machine learning", "data engineering"],
    "docker": ["kubernetes", "devops", "ci/cd"],
    "kubernetes": ["docker", "cloud architecture", "devops"],
    "aws": ["cloud architecture", "devops", "security"],
    "sql": ["data engineering", "mongodb"],
    "mongodb": ["sql", "data engineering"],
    "security": ["devops", "cloud architecture"],
    "api design": ["fastapi", "node.js", "rest"],
}

MIN_CONFIDENCE_FOR_DIRECT_MATCH = 40.0
MIN_CONFIDENCE_FOR_ADJACENT_MATCH = 55.0  # need to be reasonably strong elsewhere to count as transferable


def predict_adjacent_skills(employee_skills: Dict[str, float]) -> Dict[str, float]:
    """
    Given {skill: confidence_score}, return {adjacent_skill: inherited_confidence}
    for skills the employee doesn't directly have evidence for, inherited at 60%
    of the source skill's confidence.
    """
    inherited = {}
    for skill, score in employee_skills.items():
        if score < MIN_CONFIDENCE_FOR_ADJACENT_MATCH:
            continue
        for adj in ADJACENCY_MAP.get(skill, []):
            if adj not in employee_skills:
                inherited[adj] = max(inherited.get(adj, 0), score * 0.6)
    return inherited


def score_employee_for_project(employee: dict, required_skills: List[str]) -> dict:
    """
    Returns match details for one employee against a project's required skills.
    """
    skill_map = {s["skill"]: s["confidence_score"] for s in employee.get("skills", [])}
    adjacent = predict_adjacent_skills(skill_map)

    matched_skills, adjacent_skills, breakdown = [], [], {}
    total = 0.0
    for req in required_skills:
        if req in skill_map and skill_map[req] >= MIN_CONFIDENCE_FOR_DIRECT_MATCH:
            matched_skills.append(req)
            breakdown[req] = skill_map[req]
            total += skill_map[req]
        elif req in adjacent:
            adjacent_skills.append(req)
            breakdown[req] = round(adjacent[req], 2)
            total += adjacent[req]
        else:
            breakdown[req] = skill_map.get(req, 0.0)
            total += skill_map.get(req, 0.0)

    match_score = round(total / max(len(required_skills), 1), 2)

    evidence_highlights = []
    for s in employee.get("skills", []):
        if s["skill"] in required_skills and s.get("evidence"):
            top = s["evidence"][0]
            evidence_highlights.append(f"{s['skill']}: {top.get('snippet', '')[:120]}")

    return {
        "employee_id": str(employee["_id"]),
        "name": employee["name"],
        "matched_skills": matched_skills,
        "adjacent_skills": adjacent_skills,
        "match_score": match_score,
        "skill_breakdown": breakdown,
        "evidence_highlights": evidence_highlights[:5],
    }


def form_shadow_squad(scored_candidates: List[dict], required_skills: List[str], max_squad_size: int = 5) -> List[dict]:
    """
    Greedy set-cover: repeatedly pick the candidate who covers the most
    still-uncovered required skills (direct or adjacent), tie-broken by match_score,
    until all skills are covered or we hit max_squad_size.
    """
    remaining = set(required_skills)
    pool = sorted(scored_candidates, key=lambda c: c["match_score"], reverse=True)
    squad = []
    used_ids = set()

    while remaining and len(squad) < max_squad_size:
        best, best_cover = None, -1
        for c in pool:
            if c["employee_id"] in used_ids:
                continue
            covers = remaining.intersection(set(c["matched_skills"]) | set(c["adjacent_skills"]))
            if len(covers) > best_cover:
                best, best_cover = c, len(covers)
        if not best or best_cover <= 0:
            break
        squad.append(best)
        used_ids.add(best["employee_id"])
        remaining -= (set(best["matched_skills"]) | set(best["adjacent_skills"]))

    # If squad is still empty (no one covers anything), fall back to top overall match_score
    if not squad and pool:
        squad = pool[:min(3, len(pool))]

    return squad
