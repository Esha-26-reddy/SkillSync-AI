"""
Lightweight keyword/pattern-based skill extractor.

Extracts technical skills from:
- GitHub commit messages
- Changed filenames
- Pull request titles and descriptions
- Jira/ServiceNow tickets
"""

import re
from typing import List


# skill -> keywords/regex patterns that indicate that skill was used
SKILL_KEYWORDS = {
    # Programming Languages
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

    # Frontend
    "react": [
        r"\breact\b",
        r"\.jsx\b",
        r"\.tsx\b",
        r"\buse[A-Z][a-zA-Z]*\(",
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

    # Backend
    "fastapi": [
        r"\bfastapi\b",
        r"\buvicorn\b",
    ],

    "node.js": [
        r"\bnode\.?js\b",
        r"\bexpress\.?js\b",
    ],

    # Databases
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

    # Cloud and DevOps
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

    # AI/ML
    "machine learning": [
        r"\bmachine learning\b",
        r"\bml model\b",
        r"\bscikit\b",
        r"\bscikit-learn\b",
        r"\bpytorch\b",
        r"\btensorflow\b",
    ],

    # Engineering
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

    # C++/Software Engineering
    "algorithms": [
        r"\balgorithm(s)?\b",
        r"\bsorting\b",
        r"\bsearching\b",
        r"\bgraph\b",
        r"\bdynamic programming\b",
        r"\bdata structure(s)?\b",
    ],
}


# Keywords used to estimate the complexity of a contribution
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


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract technical skills from free text.

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


def estimate_complexity_weight(
    text: str,
    lines_changed: int = 0
) -> float:
    """
    Returns a complexity weight between 0.0 and 1.0.

    Complexity is estimated using:
    - Commit/PR text
    - Keywords
    - Number of changed lines
    """

    text_lower = (text or "").lower()

    # Baseline complexity
    weight = 0.3

    # High complexity work
    if any(
        re.search(pattern, text_lower)
        for pattern in COMPLEXITY_KEYWORDS_HIGH
    ):
        weight = max(weight, 0.9)

    # Medium complexity work
    elif any(
        re.search(pattern, text_lower)
        for pattern in COMPLEXITY_KEYWORDS_MED
    ):
        weight = max(weight, 0.6)

    # Complexity based on code size
    if lines_changed:

        if lines_changed > 300:
            weight = max(weight, 0.95)

        elif lines_changed > 100:
            weight = max(weight, 0.7)

        elif lines_changed > 30:
            weight = max(weight, 0.5)

    return min(weight, 1.0)