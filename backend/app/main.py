from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import seed_learning_resources_if_empty
from app.routers import auth, employees, github_integration, mock_data, projects

app = FastAPI(
    title="SkillSync AI API",
    description="Turns employees' real work contributions into verified skill profiles, "
                 "matches them to project requirements, and forms Shadow Squads.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(github_integration.router)
app.include_router(mock_data.router)
app.include_router(projects.router)


@app.on_event("startup")
def on_startup():
    seed_learning_resources_if_empty()


@app.get("/")
def root():
    return {"status": "ok", "service": "SkillSync AI API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
