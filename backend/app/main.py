from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import seed_learning_resources_if_empty
from app.routers import (
    auth,
    employees,
    github_integration,
    mock_data,
    projects,
)


app = FastAPI(
    title="SkillSync AI API",
    description=(
        "Turns employees' real work contributions into verified skill profiles, "
        "matches them to project requirements, and forms Shadow Squads."
    ),
    version="1.0.0",
)


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        # Deployed frontend
        "https://skillsync-ai-frontend.onrender.com",

        # Local frontend development
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# ROUTERS
# --------------------------------------------------

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(github_integration.router)
app.include_router(mock_data.router)
app.include_router(projects.router)


# --------------------------------------------------
# STARTUP
# --------------------------------------------------

@app.on_event("startup")
def on_startup():
    seed_learning_resources_if_empty()


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "SkillSync AI API",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }