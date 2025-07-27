"""JWT-based authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core import (
    success,
    StandardResponse,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.db.database import get_db
from app.repositories import user as user_repo
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=StandardResponse, summary="Login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = user_repo.get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.user_id)
    return success(TokenResponse(access_token=token)).dict()


@router.post("/logout", response_model=StandardResponse, summary="Logout")
def logout(authorization: str = Header(..., alias="Authorization")) -> dict:
    token = authorization.replace("Bearer ", "")
    try:
        decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    return success({"detail": "logout successful"}).dict()


@router.post("/verify", response_model=StandardResponse, summary="Verify token")
def verify(authorization: str = Header(..., alias="Authorization")) -> dict:
    token = authorization.replace("Bearer ", "")
    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    return success({"user_id": str(user_id)}).dict()
