import random
from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from app.database import employees_col, contributions_col
from app.models import MockDataSeedRequest
from app.services.skill_extractor import extract_skills_from_text, estimate_complexity_weight
from app.services.skill_recompute import recompute_employee_skills
from app.auth import get_current_user

router = APIRouter(prefix="/mock-data", tags=["mock-integrations"], dependencies=[Depends(get_current_user)])

# Realistic-sounding ticket templates. Each maps naturally to skills via the
# same keyword extractor used for GitHub text, so Jira/ServiceNow evidence
# feeds into the same Verified Skill Graph.
JIRA_TEMPLATES = [
    "Fix authentication bug in login API endpoint (FastAPI + JWT)",
    "Optimize MongoDB query performance for reporting dashboard",
    "Implement new React component for the analytics dashboard",
    "Set up CI/CD pipeline with GitHub Actions for staging deploys",
    "Migrate service to Kubernetes for better scalability",
    "Write unit tests (pytest) for the skill-matching microservice",
    "Refactor Node.js payment service for better error handling",
    "Investigate security vulnerability in API rate limiting",
    "Add TypeScript types across the frontend codebase",
    "Build ETL data pipeline to sync data from ServiceNow",
    "Deploy new microservice to AWS Lambda with S3 integration",
    "Design REST API schema for the new integrations module",
]

SERVICENOW_TEMPLATES = [
    "Resolve incident: production API outage due to database connection pool exhaustion",
    "Change request: upgrade Docker base images across all services for security patch",
    "Incident: Kubernetes pod crash-looping in production, root cause analysis required",
    "Change request: rotate AWS IAM credentials and update security policies",
    "Incident: high latency reported on React dashboard, investigate frontend performance",
]

PRIORITY_WEIGHT = {"P1": 0.95, "P2": 0.75, "P3": 0.5, "P4": 0.3}


@router.post("/seed")
def seed_mock_data(payload: MockDataSeedRequest):
    """
    Generates realistic mock Jira and ServiceNow contribution records for an
    employee (since we don't have live Jira/ServiceNow credentials in this
    demo), stores them alongside real GitHub contributions, and recomputes
    the Verified Skill Graph the same way for both sources.
    """
    try:
        emp = employees_col.find_one({"_id": ObjectId(payload.employee_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid employee id")
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    inserted = 0

    for i in range(payload.num_jira_tickets):
        text = random.choice(JIRA_TEMPLATES)
        priority = random.choice(list(PRIORITY_WEIGHT.keys()))
        days_ago = random.randint(1, 180)
        skills = extract_skills_from_text(text)
        if not skills:
            continue
        complexity = max(estimate_complexity_weight(text), PRIORITY_WEIGHT[priority])
        peer_validated = random.random() < 0.5  # e.g. ticket reviewed/approved by lead

        contributions_col.insert_one({
            "employee_id": payload.employee_id,
            "source": "jira",
            "ref": f"JIRA-{random.randint(1000,9999)}-{i}",
            "text": f"[{priority}] {text}",
            "date": datetime.utcnow() - timedelta(days=days_ago),
            "skills_detected": skills,
            "complexity_weight": complexity,
            "peer_validated": peer_validated,
        })
        inserted += 1

    for i in range(payload.num_servicenow_tickets):
        text = random.choice(SERVICENOW_TEMPLATES)
        days_ago = random.randint(1, 180)
        skills = extract_skills_from_text(text)
        if not skills:
            continue
        complexity = estimate_complexity_weight(text)
        peer_validated = random.random() < 0.6  # incidents usually reviewed in postmortems

        contributions_col.insert_one({
            "employee_id": payload.employee_id,
            "source": "servicenow",
            "ref": f"INC-{random.randint(100000,999999)}-{i}",
            "text": text,
            "date": datetime.utcnow() - timedelta(days=days_ago),
            "skills_detected": skills,
            "complexity_weight": complexity,
            "peer_validated": peer_validated,
        })
        inserted += 1

    skills = recompute_employee_skills(payload.employee_id)
    return {"ingested_contributions": inserted, "skills": skills}
