from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from app.models import UserRegister, Token
from app.database import users_col
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(payload: UserRegister):
    if users_col.find_one({"username": payload.username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    users_col.insert_one({
        "username": payload.username,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
    })
    token = create_access_token({"sub": payload.username, "role": payload.role})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_col.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": user["username"], "role": user.get("role", "manager")})
    return Token(access_token=token)
