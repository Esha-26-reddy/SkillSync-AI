import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (
    create_access_token,
    hash_password,
    pwd_context,
)
from app.database import users_col
from app.models import Token, UserRegister

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

logger = logging.getLogger(__name__)


@router.post("/register", response_model=Token)
def register(payload: UserRegister):

    existing_user = users_col.find_one(
        {"username": payload.username},
        {"_id": 1},
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    password_hash = hash_password(payload.password)

    users_col.insert_one(
        {
            "username": payload.username,
            "password_hash": password_hash,
            "role": payload.role,
        }
    )

    token = create_access_token(
        {
            "sub": payload.username,
            "role": payload.role,
        }
    )

    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    total_start = time.perf_counter()

    db_start = time.perf_counter()

    user = users_col.find_one(
        {"username": form_data.username},
        {
            "_id": 0,
            "username": 1,
            "password_hash": 1,
            "role": 1,
        },
    )

    db_time = time.perf_counter() - db_start

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    verify_start = time.perf_counter()

    valid, new_hash = pwd_context.verify_and_update(
        form_data.password,
        user["password_hash"],
    )

    verify_time = time.perf_counter() - verify_start

    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    if new_hash:
        users_col.update_one(
            {"username": user["username"]},
            {
                "$set": {
                    "password_hash": new_hash,
                }
            },
        )

    token = create_access_token(
        {
            "sub": user["username"],
            "role": user.get("role", "manager"),
        }
    )

    total_time = time.perf_counter() - total_start

    logger.info(f"MongoDB query: {db_time:.4f}s")
    logger.info(f"Password verify: {verify_time:.4f}s")
    logger.info(f"Total login: {total_time:.4f}s")

    return Token(access_token=token)