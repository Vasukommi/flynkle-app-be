"""Authentication placeholder endpoints."""

from fastapi import APIRouter

from app.core import success, StandardResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=StandardResponse, summary="Login placeholder")
def login() -> dict:
    return success({"detail": "login successful"}).dict()

@router.post("/logout", response_model=StandardResponse, summary="Logout placeholder")
def logout() -> dict:
    return success({"detail": "logout successful"}).dict()

@router.post("/verify", response_model=StandardResponse, summary="Verification placeholder")
def verify() -> dict:
    return success({"detail": "verification successful"}).dict()
