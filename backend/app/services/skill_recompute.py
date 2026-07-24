from bson import ObjectId
from bson.errors import InvalidId
from collections import defaultdict

from app.database import employees_col, contributions_col
from app.services.confidence_calculator import calculate_skill_confidence


def normalize_skill(skill: str) -> str:
    """
    Converts skill names into a consistent format.
    """

    skill = skill.lower().strip()

    aliases = {
        "rest apis": "rest api",
        "restful api": "rest api",
        "restful apis": "rest api",
        "ml": "machine learning",
        "js": "javascript",
        "ts": "typescript",
        "mongo": "mongodb",
        "node": "node.js",
    }

    return aliases.get(skill, skill)


def recompute_employee_skills(employee_id: str):
    """
    Reads all stored contributions for an employee,
    groups evidence by skill, recalculates confidence scores,
    and saves the Verified Skill Graph.
    """

    # Validate employee ID
    try:
        employee_object_id = ObjectId(employee_id)
    except Exception:
        raise ValueError("Invalid employee ID")

    # Check employee exists
    employee = employees_col.find_one(
        {"_id": employee_object_id}
    )

    if not employee:
        raise ValueError("Employee not found")

    # Contributions currently store employee_id as a string
    contributions = list(
        contributions_col.find(
            {"employee_id": employee_id}
        )
    )

    skill_evidence = defaultdict(list)

    for contribution in contributions:

        detected_skills = contribution.get(
            "skills_detected",
            []
        )

        for skill in detected_skills:

            normalized_skill = normalize_skill(skill)

            skill_evidence[normalized_skill].append(
                {
                    "date": contribution.get(
                        "date"
                    ),

                    "weight": contribution.get(
                        "complexity_weight",
                        0.3
                    ),

                    "peer_validated": contribution.get(
                        "peer_validated",
                        False
                    ),

                    "source": contribution.get(
                        "source",
                        "unknown"
                    ),

                    "snippet": contribution.get(
                        "text",
                        ""
                    )[:300],
                }
            )

    skills_out = []

    for skill, evidence in skill_evidence.items():

        scores = calculate_skill_confidence(
            evidence
        )

        skills_out.append(
            {
                "skill": skill,

                **scores,

                "evidence_count": len(
                    evidence
                ),

                "evidence": sorted(
                    evidence,
                    key=lambda e: e.get(
                        "date"
                    ) or "",
                    reverse=True
                )[:10],
            }
        )

    skills_out.sort(
        key=lambda skill: skill.get(
            "confidence_score",
            0
        ),
        reverse=True
    )

    # Save verified skills
    employees_col.update_one(
        {
            "_id": employee_object_id
        },
        {
            "$set": {
                "skills": skills_out
            }
        }
    )

    return skills_out