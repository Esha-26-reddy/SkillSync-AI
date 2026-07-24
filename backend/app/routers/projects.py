from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from app.models import ProjectCreate
from app.database import projects_col, employees_col
from app.auth import get_current_user
from app.services.matcher import score_employee_for_project, form_shadow_squad
from app.services.learning_plan import generate_bridge_learning_plan

router = APIRouter(prefix="/projects", tags=["projects"], dependencies=[Depends(get_current_user)])


def _serialize(project: dict) -> dict:
    project = dict(project)
    project["id"] = str(project["_id"])
    del project["_id"]
    return project


@router.post("")
def create_project(payload: ProjectCreate):
    doc = payload.model_dump()
    doc["last_match_result"] = None
    result = projects_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


@router.get("")
def list_projects():
    return [_serialize(p) for p in projects_col.find({})]


@router.get("/{project_id}")
def get_project(project_id: str):
    try:
        project = projects_col.find_one({"_id": ObjectId(project_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid project id")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _serialize(project)


@router.delete("/{project_id}")
def delete_project(project_id: str):
    try:
        result = projects_col.delete_one({"_id": ObjectId(project_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid project id")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True}


@router.post("/{project_id}/match")
def match_project(project_id: str):
    """
    Core SkillSync AI workflow for an existing project:
      match skills + calculate confidence -> predict adjacent skills
      -> form Shadow Squad (greedy set-cover) -> generate Bridge Learning
      Plan with evidence-backed, explainable recommendations.
    """
    try:
        project = projects_col.find_one({"_id": ObjectId(project_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid project id")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    required_skills = project["required_skills"]

    candidates = [
        score_employee_for_project(emp, required_skills)
        for emp in employees_col.find({})
    ]
    candidates.sort(key=lambda c: c["match_score"], reverse=True)

    shadow_squad = form_shadow_squad(candidates, required_skills)
    squad_ids = {m["employee_id"] for m in shadow_squad}
    other_candidates = [c for c in candidates if c["employee_id"] not in squad_ids]

    bridge_learning_plan = generate_bridge_learning_plan(required_skills, shadow_squad)

    result = {
        "shadow_squad": shadow_squad,
        "other_candidates": other_candidates,
        "bridge_learning_plan": bridge_learning_plan,
    }

    projects_col.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {"last_match_result": result}},
    )
    return result
