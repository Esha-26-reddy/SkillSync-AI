"""
Hybrid AI-powered skill extractor.

Extracts technical skills from:
- GitHub commit messages
- Changed filenames
- Pull request titles and descriptions
- Jira/ServiceNow tickets

Uses:
1. Keyword/pattern-based extraction for fast deterministic detection.
2. Gemini AI for contextual semantic skill extraction.
3. Complexity estimation for contribution scoring.
"""

import json
import re
from typing import Dict, List

from google import genai

from app.config import settings


# =========================================================
# GEMINI CLIENT
# =========================================================

# Initialize Gemini only if an API key is available.
# This allows the keyword extractor to continue working
# even if Gemini is unavailable.
gemini_client = None

if settings.GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )


# =========================================================
# KEYWORD-BASED SKILL EXTRACTION
# =========================================================

# skill -> keywords/regex patterns that indicate that skill was used
SKILL_KEYWORDS = {

    # -----------------------------------------------------
    # Programming Languages
    # -----------------------------------------------------

    "python": [
        r"\bpython\b",
        r"\.py\b",
        r"\bpip\b",
        r"\bdjango\b",
        r"\bflask\b",
        r"\bfastapi\b",
    ],

    "javascript": [
        r"\bjavascript\b",
        r"\.js\b",
        r"\bnode\b",
        r"\bnpm\b",
    ],

    "typescript": [
        r"\btypescript\b",
        r"\.ts\b",
        r"\.tsx\b",
    ],

    "java": [
        r"\bjava\b",
        r"\.java\b",
        r"\bspring\b",
        r"\bspringboot\b",
        r"\bspring boot\b",
    ],

    "c++": [
        r"\bc\+\+\b",
        r"\.cpp\b",
        r"\.cc\b",
        r"\.cxx\b",
        r"\.hpp\b",
    ],

    "c": [
        r"\.c\b",
    ],

    "c#": [
        r"\bc#\b",
        r"\.cs\b",
        r"\bdotnet\b",
        r"\.net\b",
    ],

    "go": [
        r"\bgolang\b",
        r"\.go\b",
    ],

    "rust": [
        r"\brust\b",
        r"\.rs\b",
    ],


    # -----------------------------------------------------
    # Frontend
    # -----------------------------------------------------

    "react": [
        r"\breact\b",
        r"\.jsx\b",
        r"\.tsx\b",
        r"\bcomponent\b",
    ],

    "html/css": [
        r"\bhtml\b",
        r"\bcss\b",
        r"\btailwind\b",
        r"\bscss\b",
        r"\.html?\b",
        r"\.css\b",
        r"\.scss\b",
    ],


    # -----------------------------------------------------
    # Backend
    # -----------------------------------------------------

    "fastapi": [
        r"\bfastapi\b",
        r"\buvicorn\b",
    ],

    "node.js": [
        r"\bnode\.?js\b",
        r"\bexpress\.?js\b",
    ],


    # -----------------------------------------------------
    # Databases
    # -----------------------------------------------------

    "sql": [
        r"\bsql\b",
        r"\bselect .* from\b",
        r"\bpostgres\b",
        r"\bpostgresql\b",
        r"\bmysql\b",
        r"\bsqlite\b",
    ],

    "mongodb": [
        r"\bmongo(db)?\b",
        r"\bpymongo\b",
        r"\bmotor\b",
    ],


    # -----------------------------------------------------
    # Cloud and DevOps
    # -----------------------------------------------------

    "docker": [
        r"\bdocker\b",
        r"\bdockerfile\b",
        r"\bcontainer(ize|s)?\b",
    ],

    "kubernetes": [
        r"\bkubernetes\b",
        r"\bk8s\b",
        r"\bhelm\b",
        r"\bpod(s)?\b",
    ],

    "aws": [
        r"\baws\b",
        r"\bec2\b",
        r"\bs3\b",
        r"\blambda\b",
    ],

    "ci/cd": [
        r"\bci/cd\b",
        r"\bpipeline\b",
        r"\bgithub actions\b",
        r"\bjenkins\b",
    ],


    # -----------------------------------------------------
    # AI / ML
    # -----------------------------------------------------

    "machine learning": [
        r"\bmachine learning\b",
        r"\bml model\b",
        r"\bscikit\b",
        r"\bscikit-learn\b",
        r"\bpytorch\b",
        r"\btensorflow\b",
    ],


    # -----------------------------------------------------
    # Engineering
    # -----------------------------------------------------

    "devops": [
        r"\bdevops\b",
        r"\binfrastructure\b",
        r"\bterraform\b",
        r"\bansible\b",
    ],

    "security": [
        r"\bsecurity\b",
        r"\bauth(entication)?\b",
        r"\bvulnerabilit(y|ies)\b",
        r"\bencrypt(ion)?\b",
        r"\bjwt\b",
    ],

    "testing": [
        r"\btest(s|ing)?\b",
        r"\bpytest\b",
        r"\bjest\b",
        r"\bunit test\b",
    ],

    "api design": [
        r"\bapi\b",
        r"\bendpoint\b",
        r"\brest(ful)?\b",
        r"\bswagger\b",
        r"\bopenapi\b",
    ],

    "data engineering": [
        r"\betl\b",
        r"\bdata pipeline\b",
        r"\bairflow\b",
        r"\bspark\b",
    ],

    "cloud architecture": [
        r"\bcloud\b",
        r"\bazure\b",
        r"\bgcp\b",
        r"\bmicroservice(s)?\b",
    ],


    # -----------------------------------------------------
    # Algorithms / Software Engineering
    # -----------------------------------------------------

    "algorithms": [
        r"\balgorithm(s)?\b",
        r"\bsorting\b",
        r"\bsearching\b",
        r"\bgraph\b",
        r"\bdynamic programming\b",
        r"\bdata structure(s)?\b",
    ],
}


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract technical skills using keyword and regex matching.

    Example:

        "main.cpp board.cpp"
        -> ["c++"]

        "app.py FastAPI Docker"
        -> ["python", "fastapi", "docker"]
    """

    if not text:
        return []

    text_lower = text.lower()

    found = []

    for skill, patterns in SKILL_KEYWORDS.items():

        for pattern in patterns:

            if re.search(pattern, text_lower):

                found.append(skill)

                break

    return found


# =========================================================
# GEMINI AI SKILL EXTRACTION
# =========================================================

def extract_skills_with_gemini(
    text: str
) -> List[Dict]:
    """
    Extract contextual technical skills using Gemini.

    Returns:

        [
            {
                "name": "FastAPI",
                "confidence": 0.95,
                "evidence": "FastAPI middleware was implemented"
            }
        ]
    """

    if not text:

        return []


    # If Gemini API key is missing,
    # return an empty list instead of crashing.
    if gemini_client is None:

        print(
            "Gemini API key not configured. "
            "Using keyword-based extraction only."
        )

        return []


    prompt = f"""
You are an expert software engineering skill extraction system.

Analyze the following software engineering contribution.

Extract ONLY technical skills that are clearly supported
by the provided evidence.

Contribution:
{text}

Return ONLY valid JSON in exactly this format:

{{
    "skills": [
        {{
            "name": "skill name",
            "confidence": 0.0,
            "evidence": "short explanation"
        }}
    ]
}}

Rules:

1. Confidence must be between 0 and 1.
2. Do not invent unrelated skills.
3. Extract only skills supported by the contribution.
4. Identify programming languages, frameworks, databases,
   cloud technologies, security, testing, DevOps,
   architecture, algorithms, and other technical skills.
5. Evidence must be based directly on the provided contribution.
6. Keep the skill name concise.
"""


    try:

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )


        response_text = response.text.strip()


        # Remove Markdown code fences if Gemini returns them.
        response_text = re.sub(
            r"```json",
            "",
            response_text,
            flags=re.IGNORECASE
        )

        response_text = re.sub(
            r"```",
            "",
            response_text
        ).strip()


        result = json.loads(response_text)


        skills = result.get("skills", [])


        # Validate Gemini output.
        validated_skills = []

        for skill in skills:

            if not isinstance(skill, dict):

                continue


            name = skill.get("name")

            if not name:

                continue


            confidence = skill.get(
                "confidence",
                0.0
            )


            try:

                confidence = float(confidence)

            except (TypeError, ValueError):

                confidence = 0.0


            # Ensure confidence remains between 0 and 1.
            confidence = max(
                0.0,
                min(confidence, 1.0)
            )


            validated_skills.append(
                {
                    "name": name.strip(),
                    "confidence": confidence,
                    "evidence": skill.get(
                        "evidence",
                        ""
                    )
                }
            )


        return validated_skills


    except Exception as error:

        print(
            f"Gemini skill extraction failed: {error}"
        )

        return []


# =========================================================
# HYBRID SKILL EXTRACTION
# =========================================================

def extract_verified_skills(
    text: str
) -> List[Dict]:
    """
    Combines keyword-based and Gemini-based skill extraction.

    Keyword extraction:
        - Fast
        - Deterministic
        - Works without an API connection

    Gemini extraction:
        - Understands context
        - Extracts semantic technical skills
        - Provides evidence and AI confidence

    Returns:

        [
            {
                "name": "Python",
                "source": "gemini",
                "confidence": 0.95,
                "evidence": "Python backend implementation"
            }
        ]
    """

    if not text:

        return []


    # ---------------------------------------------
    # 1. Keyword-based extraction
    # ---------------------------------------------

    keyword_skills = extract_skills_from_text(text)


    # ---------------------------------------------
    # 2. Gemini-based extraction
    # ---------------------------------------------

    gemini_skills = extract_skills_with_gemini(text)


    # ---------------------------------------------
    # 3. Merge and deduplicate
    # ---------------------------------------------

    merged_skills = {}


    # Add keyword-based skills first.
    for skill in keyword_skills:

        normalized_name = skill.lower().strip()

        merged_skills[normalized_name] = {

            "name": skill,

            "source": "keyword",

            "confidence": None,

            "evidence": (
                "Detected from contribution "
                "text using keyword patterns."
            )
        }


    # Add Gemini skills.
    # If Gemini identifies the same skill,
    # its contextual information replaces the
    # simpler keyword information.
    for skill in gemini_skills:

        skill_name = skill.get(
            "name",
            ""
        ).strip()


        if not skill_name:

            continue


        normalized_name = skill_name.lower()


        merged_skills[normalized_name] = {

            "name": skill_name,

            "source": "gemini",

            "confidence": skill.get(
                "confidence",
                0.0
            ),

            "evidence": skill.get(
                "evidence",
                ""
            )
        }


    return list(
        merged_skills.values()
    )


# =========================================================
# COMPLEXITY ESTIMATION
# =========================================================

COMPLEXITY_KEYWORDS_HIGH = [

    r"\brefactor\b",

    r"\barchitecture\b",

    r"\bmigration\b",

    r"\boptimi[sz]e\b",

    r"\bconcurrency\b",

    r"\bperformance\b",

    r"\bsecurity\b",

    r"\bscal(e|ing|ability)\b",

    r"\balgorithm\b",
]


COMPLEXITY_KEYWORDS_MED = [

    r"\bfeature\b",

    r"\bintegration\b",

    r"\bapi\b",

    r"\bbug ?fix\b",

    r"\bimplement\b",

    r"\badd\b",
]


def estimate_complexity_weight(
    text: str,
    lines_changed: int = 0
) -> float:
    """
    Returns a complexity weight between 0.0 and 1.0.

    Complexity is estimated using:

    - Commit / PR text
    - Complexity keywords
    - Number of changed lines

    Baseline:
        0.3

    Medium complexity:
        0.6

    High complexity:
        0.9

    Large code changes:
        Up to 0.95
    """

    text_lower = (
        text or ""
    ).lower()


    # ---------------------------------------------
    # Baseline complexity
    # ---------------------------------------------

    weight = 0.3


    # ---------------------------------------------
    # High-complexity work
    # ---------------------------------------------

    if any(

        re.search(
            pattern,
            text_lower
        )

        for pattern in COMPLEXITY_KEYWORDS_HIGH

    ):

        weight = max(
            weight,
            0.9
        )


    # ---------------------------------------------
    # Medium-complexity work
    # ---------------------------------------------

    elif any(

        re.search(
            pattern,
            text_lower
        )

        for pattern in COMPLEXITY_KEYWORDS_MED

    ):

        weight = max(
            weight,
            0.6
        )


    # ---------------------------------------------
    # Complexity based on changed lines
    # ---------------------------------------------

    if lines_changed:

        if lines_changed > 300:

            weight = max(
                weight,
                0.95
            )

        elif lines_changed > 100:

            weight = max(
                weight,
                0.7
            )

        elif lines_changed > 30:

            weight = max(
                weight,
                0.5
            )


    return min(
        weight,
        1.0
    )