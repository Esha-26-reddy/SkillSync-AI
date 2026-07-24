"""
Implements the Skill Confidence Score formula from the deck:

    Score = 0.30 * Frequency + 0.30 * Complexity + 0.20 * Recency + 0.20 * PeerValidation

Each component is normalized to a 0-100 scale before weighting, so the final
Score is also on a 0-100 scale.
"""
import math
from datetime import datetime
from typing import List, Dict

FREQUENCY_WEIGHT = 0.30
COMPLEXITY_WEIGHT = 0.30
RECENCY_WEIGHT = 0.20
PEER_VALIDATION_WEIGHT = 0.20

# A skill needs roughly this many pieces of evidence to be considered "fully frequent"
FREQUENCY_SATURATION_COUNT = 15
# Recency half-life in days: contributions older than this count for much less
RECENCY_HALF_LIFE_DAYS = 60


def _frequency_score(evidence: List[dict]) -> float:
    count = len(evidence)
    return min(count / FREQUENCY_SATURATION_COUNT, 1.0) * 100


def _complexity_score(evidence: List[dict]) -> float:
    if not evidence:
        return 0.0
    weights = [e.get("weight", 0.3) for e in evidence]
    return (sum(weights) / len(weights)) * 100


def _recency_score(evidence: List[dict]) -> float:
    if not evidence:
        return 0.0
    now = datetime.utcnow()
    most_recent = max(e["date"] for e in evidence)
    if isinstance(most_recent, str):
        most_recent = datetime.fromisoformat(most_recent)
    days_since = max((now - most_recent).days, 0)
    decay = math.exp(-days_since / RECENCY_HALF_LIFE_DAYS)
    return decay * 100


def _peer_validation_score(evidence: List[dict]) -> float:
    if not evidence:
        return 0.0
    validated = sum(1 for e in evidence if e.get("peer_validated"))
    return min(validated / max(len(evidence) * 0.5, 1), 1.0) * 100


def calculate_skill_confidence(evidence: List[dict]) -> Dict[str, float]:
    """
    evidence: list of dicts like:
        {"date": datetime, "weight": 0.0-1.0, "peer_validated": bool}

    Returns a dict with each sub-score plus the final weighted confidence_score,
    all on a 0-100 scale, so the frontend / API can show the breakdown
    (this is what powers "Explainable AI recommendations").
    """
    frequency = _frequency_score(evidence)
    complexity = _complexity_score(evidence)
    recency = _recency_score(evidence)
    peer_validation = _peer_validation_score(evidence)

    confidence = (
        FREQUENCY_WEIGHT * frequency
        + COMPLEXITY_WEIGHT * complexity
        + RECENCY_WEIGHT * recency
        + PEER_VALIDATION_WEIGHT * peer_validation
    )

    return {
        "frequency_score": round(frequency, 2),
        "complexity_score": round(complexity, 2),
        "recency_score": round(recency, 2),
        "peer_validation_score": round(peer_validation, 2),
        "confidence_score": round(confidence, 2),
    }
