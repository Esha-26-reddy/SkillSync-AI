from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from app.models import EmployeeCreate
from app.database import employees_col
from app.auth import get_current_user

router = APIRouter(prefix="/employees", tags=["employees"], dependencies=[Depends(get_current_user)])


def _serialize(emp: dict) -> dict:
    emp["id"] = str(emp["_id"])
    del emp["_id"]
    return emp


@router.post("")
def create_employee(payload: EmployeeCreate):
    if employees_col.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Employee with this email already exists")
    doc = payload.model_dump()
    doc["skills"] = []
    result = employees_col.insert_one(doc)  # pymongo injects "_id" into doc in place
    doc.pop("_id", None)
    return {"id": str(result.inserted_id), **doc}


@router.get("")
def list_employees():
    return [_serialize(e) for e in employees_col.find({})]


@router.get("/{employee_id}")
def get_employee(employee_id: str):
    try:
        emp = employees_col.find_one({"_id": ObjectId(employee_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid employee id")
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return _serialize(emp)


@router.get("/{employee_id}/skill-graph")
def get_skill_graph(employee_id: str):
    """Returns the Verified Skill Graph: skills ranked by confidence, with evidence."""
    try:
        emp = employees_col.find_one({"_id": ObjectId(employee_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid employee id")
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    skills = sorted(emp.get("skills", []), key=lambda s: s["confidence_score"], reverse=True)
    return {
        "employee_id": employee_id,
        "name": emp["name"],
        "skills": skills,
    }


@router.delete("/{employee_id}")
def delete_employee(employee_id: str):
    try:
        result = employees_col.delete_one({"_id": ObjectId(employee_id)})
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid employee id")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"deleted": True}
