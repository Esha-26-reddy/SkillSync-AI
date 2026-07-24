from typing import List, Optional
from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str
    role: str = "manager"  # "manager" or "employee"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmployeeCreate(BaseModel):
    name: str
    email: str
    title: Optional[str] = None
    github_username: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    required_skills: List[str]


class MockDataSeedRequest(BaseModel):
    employee_id: str
    num_jira_tickets: int = 10
    num_servicenow_tickets: int = 5


class GithubSyncRequest(BaseModel):
    employee_id: str
    github_username: str
    repo: str  # "owner/repo"
    max_items: int = 50
