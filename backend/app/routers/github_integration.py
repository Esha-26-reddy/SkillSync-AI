from datetime import datetime

import requests
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from app.config import settings
from app.models import GithubSyncRequest
from app.database import employees_col, contributions_col
from app.services.skill_extractor import (
    extract_skills_from_text,
    estimate_complexity_weight,
)
from app.services.skill_recompute import recompute_employee_skills
from app.auth import get_current_user


router = APIRouter(
    prefix="/github",
    tags=["github"],
    dependencies=[Depends(get_current_user)],
)


GITHUB_API = "https://api.github.com"


def _headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json"
    }

    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    return headers


def _parse_date(date_str: str | None) -> datetime:

    if not date_str:
        return datetime.utcnow()

    return datetime.fromisoformat(
        date_str.replace("Z", "+00:00")
    ).replace(tzinfo=None)


def _fetch_commits(
    repo: str,
    author: str,
    max_items: int
) -> list:

    response = requests.get(
        f"{GITHUB_API}/repos/{repo}/commits",
        params={
            "author": author,
            "per_page": min(max_items, 100),
        },
        headers=_headers(),
        timeout=15,
    )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{repo}' not found or not accessible",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"GitHub commits fetch failed: {response.text[:200]}",
        )

    return response.json()


def _fetch_pull_requests(
    repo: str,
    author: str,
    max_items: int
) -> list:

    response = requests.get(
        f"{GITHUB_API}/search/issues",
        params={
            "q": f"repo:{repo} type:pr author:{author}",
            "per_page": min(max_items, 100),
        },
        headers=_headers(),
        timeout=15,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"GitHub PR search failed: {response.text[:200]}",
        )

    return response.json().get("items", [])


def _pr_has_approval(
    repo: str,
    pr_number: int
) -> bool:

    response = requests.get(
        f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/reviews",
        headers=_headers(),
        timeout=15,
    )

    if response.status_code != 200:
        return False

    return any(
        review.get("state") == "APPROVED"
        for review in response.json()
    )


def _pr_changed_files(
    repo: str,
    pr_number: int
) -> list[str]:

    response = requests.get(
        f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/files",
        headers=_headers(),
        timeout=15,
    )

    if response.status_code != 200:
        return []

    return [
        file.get("filename", "")
        for file in response.json()
    ]


@router.post("/sync")
def sync_github(
    payload: GithubSyncRequest
):

    # Validate employee ID
    try:

        employee = employees_col.find_one(
            {
                "_id": ObjectId(
                    payload.employee_id
                )
            }
        )

    except InvalidId:

        raise HTTPException(
            status_code=400,
            detail="Invalid employee id",
        )

    if not employee:

        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )


    inserted = 0


    # -------------------------------------------------
    # FETCH COMMITS
    # -------------------------------------------------

    commits = _fetch_commits(
        payload.repo,
        payload.github_username,
        payload.max_items,
    )


    for commit in commits:

        commit_sha = commit.get("sha")

        commit_message = (
            commit
            .get("commit", {})
            .get("message", "")
        )


        lines_changed = 0
        filenames = []


        # Fetch commit details
        detail_url = commit.get("url")

        if detail_url:

            detail_response = requests.get(
                detail_url,
                headers=_headers(),
                timeout=15,
            )

            if detail_response.status_code == 200:

                details = detail_response.json()

                lines_changed = (
                    details
                    .get("stats", {})
                    .get("total", 0)
                )

                filenames = [
                    file.get("filename", "")
                    for file in details.get("files", [])
                ]


        extraction_text = (
            f"{commit_message} "
            f"{' '.join(filenames)}"
        )


        skills = extract_skills_from_text(
            extraction_text
        )


        # Ignore commits where no technical skill can be detected
        if not skills:
            continue


        # Prevent duplicate commit contributions
        existing = contributions_col.find_one(
            {
                "employee_id": payload.employee_id,
                "source": "github",
                "ref": commit_sha[:12],
            }
        )


        if existing:

            continue


        contributions_col.insert_one(
            {
                "employee_id": payload.employee_id,
                "source": "github",
                "ref": commit_sha[:12],
                "repo": payload.repo,
                "text": commit_message,
                "date": _parse_date(
                    commit
                    .get("commit", {})
                    .get("author", {})
                    .get("date")
                ),
                "skills_detected": skills,
                "complexity_weight": estimate_complexity_weight(
                    extraction_text,
                    lines_changed,
                ),
                "peer_validated": False,
            }
        )


        inserted += 1


    # -------------------------------------------------
    # FETCH PULL REQUESTS
    # -------------------------------------------------

    pull_requests = _fetch_pull_requests(
        payload.repo,
        payload.github_username,
        payload.max_items,
    )


    for pr in pull_requests:

        pr_number = pr.get("number")

        if not pr_number:

            continue


        pr_title = pr.get("title", "")
        pr_body = pr.get("body") or ""


        pr_text = (
            f"{pr_title}\n"
            f"{pr_body}"
        )


        changed_files = _pr_changed_files(
            payload.repo,
            pr_number,
        )


        extraction_text = (
            f"{pr_text} "
            f"{' '.join(changed_files)}"
        )


        skills = extract_skills_from_text(
            extraction_text
        )


        if not skills:

            continue


        approved = _pr_has_approval(
            payload.repo,
            pr_number,
        )


        existing = contributions_col.find_one(
            {
                "employee_id": payload.employee_id,
                "source": "github_pr",
                "ref": f"PR-{pr_number}",
            }
        )


        if existing:

            continue


        contributions_col.insert_one(
            {
                "employee_id": payload.employee_id,
                "source": "github_pr",
                "ref": f"PR-{pr_number}",
                "repo": payload.repo,
                "text": pr_text[:500],
                "date": _parse_date(
                    pr.get("created_at")
                ),
                "skills_detected": skills,
                "complexity_weight": estimate_complexity_weight(
                    extraction_text
                ),
                "peer_validated": approved,
            }
        )


        inserted += 1


    # Save GitHub username
    employees_col.update_one(
        {
            "_id": ObjectId(
                payload.employee_id
            )
        },
        {
            "$set": {
                "github_username": payload.github_username
            }
        }
    )


    # Recompute skill graph
    skills = recompute_employee_skills(
        payload.employee_id
    )


    return {
        "ingested_contributions": inserted,
        "skills": skills,
    }