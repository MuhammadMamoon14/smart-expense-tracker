"""
auth.py — Register & login endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.file_db import read_json, write_json, generate_id, DB_FILES
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.schemas.auth import UserRegister, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister):
    users = read_json(DB_FILES["users"])

    if any(u["username"] == payload.username for u in users):
        raise HTTPException(status_code=400, detail="Username already taken")
    if any(u["email"] == payload.email for u in users):
        raise HTTPException(status_code=400, detail="Email already registered")

    now = datetime.now(timezone.utc).isoformat()
    new_user = {
        "id": generate_id(),
        "username": payload.username,
        "email": payload.email,
        "full_name": payload.full_name,
        "hashed_password": hash_password(payload.password),
        "created_at": now,
        "updated_at": now,
    }
    users.append(new_user)
    write_json(DB_FILES["users"], users)

    return UserOut(
        id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"],
        full_name=new_user["full_name"],
        created_at=new_user["created_at"],
    )


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    users = read_json(DB_FILES["users"])
    user = next((u for u in users if u["username"] == form_data.username), None)

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token({"sub": user["id"]})
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"],
    )


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        created_at=current_user["created_at"],
    )
