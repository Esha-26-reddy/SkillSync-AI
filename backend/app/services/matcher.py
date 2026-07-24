"""
Matches employees to a project's required skills.

Features:
- Case-insensitive skill matching
- Skill alias normalization
- Direct skill matching
- Adjacent/transferable skill prediction
- Confidence-based scoring
- Evidence highlights
- Greedy Shadow Squad formation
"""

from typing import Dict, List


# ============================================================
# SKILL NORMALIZATION
# ============================================================

def normalize_skill(skill: str) -> str:
    """
    Converts different representations of the same skill
    into one consistent format.

    Examples:
        React       -> react
        FASTAPI     -> fastapi
        REST APIs   -> rest api
        ML          -> machine learning
        JS          -> javascript
        Node        -> node.js
    """

    if not skill:
        return ""

    skill = skill.lower().strip()

    aliases = {
        # REST API variations
        "rest apis": "rest api",
        "restful api": "rest api",
        "restful apis": "rest api",
        "rest-api": "rest api",

        # Machine Learning
        "ml": "machine learning",
        "machine-learning": "machine learning",

        # JavaScript
        "js": "javascript",

        # TypeScript
        "ts": "typescript",

        # MongoDB
        "mongo": "mongodb",
        "mongo db": "mongodb",

        # Node.js
        "node": "node.js",
        "nodejs": "node.js",

        # C++
        "cpp": "c++",

        # C#
        "csharp": "c#",
        ".net": "c#",
        "dotnet": "c#",
    }

    return aliases.get(skill, skill)


# ============================================================
# ADJACENT / TRANSFERABLE SKILLS
# ============================================================

ADJACENCY_MAP = {

    "javascript": [
        "typescript",
        "react",
        "node.js",
    ],

    "typescript": [
        "javascript",
        "react",
    ],

    "react": [
        "javascript",
        "typescript",
        "html/css",
    ],

    "python": [
        "fastapi",
        "machine learning",
        "data engineering",
    ],

    "fastapi": [
        "python",
        "api design",
        "rest api",
    ],

    "docker": [
        "kubernetes",
        "devops",
        "ci/cd",
    ],

    "kubernetes": [
        "docker",
        "cloud architecture",
        "devops",
    ],

    "aws": [
        "cloud architecture",
        "devops",
        "security",
    ],

    "sql": [
        "data engineering",
        "mongodb",
    ],

    "mongodb": [
        "sql",
        "data engineering",
    ],

    "security": [
        "devops",
        "cloud architecture",
    ],

    "api design": [
        "fastapi",
        "node.js",
        "rest api",
    ],

    "rest api": [
        "api design",
        "fastapi",
        "node.js",
    ],

    "machine learning": [
        "python",
        "data engineering",
    ],

    "node.js": [
        "javascript",
        "api design",
        "rest api",
    ],
}


# ============================================================
# CONFIDENCE THRESHOLDS
# ============================================================

# Minimum confidence required for a direct skill match
MIN_CONFIDENCE_FOR_DIRECT_MATCH = 40.0

# Minimum confidence required to predict adjacent skills
MIN_CONFIDENCE_FOR_ADJACENT_MATCH = 55.0


# ============================================================
# ADJACENT SKILL PREDICTION
# ============================================================

def predict_adjacent_skills(
    employee_skills: Dict[str, float]
) -> Dict[str, float]:
    """
    Predicts skills that an employee can likely learn quickly
    based on their existing strong skills.

    Example:

        Input:
            {
                "python": 80
            }

        Output:
            {
                "fastapi": 48,
                "machine learning": 48,
                "data engineering": 48
            }

    The adjacent skill receives 60% of the source skill confidence.
    """

    inherited_skills = {}

    for skill, confidence_score in employee_skills.items():

        # Only strong skills can generate adjacent skills
        if confidence_score < MIN_CONFIDENCE_FOR_ADJACENT_MATCH:
            continue

        adjacent_skills = ADJACENCY_MAP.get(
            normalize_skill(skill),
            []
        )

        for adjacent_skill in adjacent_skills:

            normalized_adjacent_skill = normalize_skill(
                adjacent_skill
            )

            # Do not predict a skill the employee already has
            if normalized_adjacent_skill in employee_skills:
                continue

            inherited_score = confidence_score * 0.6

            inherited_skills[
                normalized_adjacent_skill
            ] = max(
                inherited_skills.get(
                    normalized_adjacent_skill,
                    0.0
                ),
                inherited_score
            )

    return inherited_skills


# ============================================================
# EMPLOYEE PROJECT MATCHING
# ============================================================

def score_employee_for_project(
    employee: dict,
    required_skills: List[str]
) -> dict:
    """
    Calculates how well an employee matches a project.

    The score is based on:

    1. Direct skill matches
    2. Adjacent/transferable skills
    3. Skill confidence scores
    """

    # --------------------------------------------------------
    # Build normalized employee skill map
    # --------------------------------------------------------

    skill_map: Dict[str, float] = {}

    for skill_data in employee.get("skills", []):

        skill_name = skill_data.get("skill")

        if not skill_name:
            continue

        normalized_skill_name = normalize_skill(
            skill_name
        )

        confidence_score = float(
            skill_data.get(
                "confidence_score",
                0.0
            )
        )

        # If the same skill appears multiple times,
        # keep the highest confidence score.
        skill_map[
            normalized_skill_name
        ] = max(
            skill_map.get(
                normalized_skill_name,
                0.0
            ),
            confidence_score
        )

    # --------------------------------------------------------
    # Predict adjacent skills
    # --------------------------------------------------------

    adjacent_skills_map = predict_adjacent_skills(
        skill_map
    )

    # --------------------------------------------------------
    # Match required skills
    # --------------------------------------------------------

    matched_skills = []
    adjacent_skills = []
    skill_breakdown = {}

    total_score = 0.0

    for required_skill in required_skills:

        normalized_required_skill = normalize_skill(
            required_skill
        )

        # ----------------------------------------------------
        # DIRECT MATCH
        # ----------------------------------------------------

        if (
            normalized_required_skill in skill_map
            and skill_map[
                normalized_required_skill
            ] >= MIN_CONFIDENCE_FOR_DIRECT_MATCH
        ):

            confidence_score = skill_map[
                normalized_required_skill
            ]

            matched_skills.append(
                required_skill
            )

            skill_breakdown[
                required_skill
            ] = round(
                confidence_score,
                2
            )

            total_score += confidence_score

        # ----------------------------------------------------
        # ADJACENT MATCH
        # ----------------------------------------------------

        elif (
            normalized_required_skill
            in adjacent_skills_map
        ):

            inherited_score = adjacent_skills_map[
                normalized_required_skill
            ]

            adjacent_skills.append(
                required_skill
            )

            skill_breakdown[
                required_skill
            ] = round(
                inherited_score,
                2
            )

            total_score += inherited_score

        # ----------------------------------------------------
        # NO MATCH
        # ----------------------------------------------------

        else:

            skill_breakdown[
                required_skill
            ] = 0.0

    # --------------------------------------------------------
    # FINAL MATCH SCORE
    # --------------------------------------------------------

    match_score = round(
        total_score
        / max(
            len(required_skills),
            1
        ),
        2
    )

    # --------------------------------------------------------
    # EVIDENCE HIGHLIGHTS
    # --------------------------------------------------------

    evidence_highlights = []

    required_skill_names = {
        normalize_skill(skill)
        for skill in required_skills
    }

    for skill_data in employee.get(
        "skills",
        []
    ):

        employee_skill = normalize_skill(
            skill_data.get(
                "skill",
                ""
            )
        )

        if (
            employee_skill
            in required_skill_names
            and skill_data.get(
                "evidence"
            )
        ):

            evidence = skill_data[
                "evidence"
            ]

            # Sort newest evidence first
            evidence = sorted(
                evidence,
                key=lambda item: item.get(
                    "date",
                    ""
                ),
                reverse=True
            )

            top_evidence = evidence[0]

            evidence_highlights.append(
                f"{skill_data.get('skill')}: "
                f"{top_evidence.get('snippet', '')[:120]}"
            )

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {
        "employee_id": str(
            employee["_id"]
        ),

        "name": employee.get(
            "name",
            "Unknown"
        ),

        "matched_skills": matched_skills,

        "adjacent_skills": adjacent_skills,

        "match_score": match_score,

        "skill_breakdown": skill_breakdown,

        "evidence_highlights": (
            evidence_highlights[:5]
        ),
    }


# ============================================================
# SHADOW SQUAD FORMATION
# ============================================================

def form_shadow_squad(
    scored_candidates: List[dict],
    required_skills: List[str],
    max_squad_size: int = 5
) -> List[dict]:
    """
    Forms a Shadow Squad using a greedy set-cover algorithm.

    At each step, selects the employee who covers the highest
    number of currently uncovered project skills.

    Direct and adjacent skills are both considered.
    """

    # Normalize all required project skills
    remaining_skills = {
        normalize_skill(skill)
        for skill in required_skills
    }

    # Sort candidates by match score
    candidate_pool = sorted(
        scored_candidates,
        key=lambda candidate: candidate.get(
            "match_score",
            0.0
        ),
        reverse=True
    )

    squad = []
    used_employee_ids = set()

    # --------------------------------------------------------
    # Greedy selection
    # --------------------------------------------------------

    while (
        remaining_skills
        and len(squad)
        < max_squad_size
    ):

        best_candidate = None
        best_coverage = set()

        for candidate in candidate_pool:

            employee_id = candidate.get(
                "employee_id"
            )

            if employee_id in used_employee_ids:
                continue

            covered_skills = {
                normalize_skill(skill)
                for skill in (
                    candidate.get(
                        "matched_skills",
                        []
                    )
                    +
                    candidate.get(
                        "adjacent_skills",
                        []
                    )
                )
            }

            current_coverage = (
                remaining_skills
                & covered_skills
            )

            # Select candidate covering the most
            # uncovered skills.
            if len(current_coverage) > len(
                best_coverage
            ):

                best_candidate = candidate

                best_coverage = (
                    current_coverage
                )

            # Tie-breaker: higher match score
            elif (
                len(current_coverage)
                == len(best_coverage)
                and len(current_coverage)
                > 0
                and best_candidate
                and candidate.get(
                    "match_score",
                    0.0
                )
                > best_candidate.get(
                    "match_score",
                    0.0
                )
            ):

                best_candidate = candidate

                best_coverage = (
                    current_coverage
                )

        # No candidate can cover any remaining skill
        if (
            not best_candidate
            or not best_coverage
        ):
            break

        # Add employee to Shadow Squad
        squad.append(
            best_candidate
        )

        used_employee_ids.add(
            best_candidate[
                "employee_id"
            ]
        )

        # Remove covered skills
        remaining_skills -= best_coverage

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    # If no employee has any matching skill,
    # return top candidates for visibility.
    if not squad and candidate_pool:

        squad = candidate_pool[
            :min(
                3,
                len(candidate_pool)
            )
        ]

    return squad