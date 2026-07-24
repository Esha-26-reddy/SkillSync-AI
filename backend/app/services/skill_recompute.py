from bson import ObjectId
from collections import defaultdict

from app.database import employees_col, contributions_col
from app.services.confidence_calculator import calculate_skill_confidence


def recompute_employee_skills(employee_id: str):
    """
    Reads every stored contribution (GitHub commits/PRs, Jira/ServiceNow tickets)
    for this employee, groups the evidence by skill, and recalculates each
    skill's confidence score using the deck's formula. Persists the result
    onto the employee document as the "Verified Skill Graph".
    """
    contributions = list(contributions_col.find({"employee_id": employee_id}))

    skill_evidence = defaultdict(list)
    for c in contributions:
        for skill in c.get("skills_detected", []):
            skill_evidence[skill].append({
                "date": c["date"],
                "weight": c.get("complexity_weight", 0.3),
                "peer_validated": c.get("peer_validated", False),
                "source": c["source"],
                "snippet": c.get("text", "")[:300],
            })

    skills_out = []
    for skill, evidence in skill_evidence.items():
        scores = calculate_skill_confidence(evidence)
        skills_out.append({
            "skill": skill,
            **scores,
            "evidence_count": len(evidence),
            "evidence": sorted(evidence, key=lambda e: e["date"], reverse=True)[:10],
        })

    skills_out.sort(key=lambda s: s["confidence_score"], reverse=True)

    employees_col.update_one(
        {"_id": ObjectId(employee_id)},
        {"$set": {"skills": skills_out}},
    )
    return skills_out
