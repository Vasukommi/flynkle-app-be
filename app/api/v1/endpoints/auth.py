from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", summary="Login placeholder")
def login() -> dict:
    return {"detail": "login successful"}

@router.post("/logout", summary="Logout placeholder")
def logout() -> dict:
    return {"detail": "logout successful"}

@router.post("/verify", summary="Verification placeholder")
def verify() -> dict:
    return {"detail": "verification successful"}
