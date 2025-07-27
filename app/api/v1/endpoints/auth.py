"""JWT-based authentication endpoints."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core import (
    success,
    StandardResponse,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    revoke_token,
    revoke_refresh_token,
)
from app.core import settings
from app.db.database import get_db
from app.repositories import user as user_repo
from app.schemas import LoginRequest, TokenResponse, UserUpdate
from app.services import (
    check_login_rate_limit,
    check_otp_rate_limit,
    generate_verification_token,
    verify_email_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=StandardResponse, summary="Login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> dict:
    check_login_rate_limit(credentials.email)
    user = user_repo.get_user_by_email(db, credentials.email)
    if not user or not verify_password(credentials.password, user.password):
        logger.warning("Failed login for %s", credentials.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active or user.is_suspended:
        logger.warning("Inactive/suspended login attempt for %s", credentials.email)
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token(user.user_id)
    refresh = create_refresh_token(user.user_id)
    user_repo.update_last_login(db, user)
    logger.info("User %s logged in", user.user_id)
    return success(TokenResponse(access_token=token, refresh_token=refresh)).dict()


@router.post("/logout", response_model=StandardResponse, summary="Logout")
def logout(
    authorization: str = Header(..., alias="Authorization"),
    refresh_token: str | None = Header(None, alias="X-Refresh-Token"),
) -> dict:
    token = authorization.replace("Bearer ", "")
    try:
        decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    revoke_token(token, settings.access_token_expire_minutes * 60)
    if refresh_token:
        revoke_refresh_token(refresh_token)
    logger.info("Token revoked")
    return success({"detail": "logout successful"}).dict()


@router.post("/verify", response_model=StandardResponse, summary="Verify token")
def verify(authorization: str = Header(..., alias="Authorization")) -> dict:
    token = authorization.replace("Bearer ", "")
    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    logger.debug("Token for %s verified", user_id)
    return success({"user_id": str(user_id)}).dict()


@router.post("/refresh", response_model=StandardResponse, summary="Refresh token")
def refresh_token_endpoint(refresh_token: str = Header(..., alias="X-Refresh-Token")) -> dict:
    try:
        user_id = decode_refresh_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    new_access = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)
    revoke_refresh_token(refresh_token)
    return success(TokenResponse(access_token=new_access, refresh_token=new_refresh)).dict()


@router.post("/request-reset", response_model=StandardResponse, summary="Request password reset")
def request_reset(data: dict, db: Session = Depends(get_db)) -> dict:
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    check_otp_rate_limit(f"reset:{email}")
    user = user_repo.get_user_by_email(db, email)
    if not user:
        return success({"detail": "reset requested"}).dict()
    from app.services.password_reset import generate_otp
    otp = generate_otp(email)
    logger.info("Password reset requested for %s", email)
    return success({"otp": otp}).dict()


@router.post("/reset-password", response_model=StandardResponse, summary="Reset password")
def reset_password(data: dict, db: Session = Depends(get_db)) -> dict:
    email = data.get("email")
    otp = data.get("otp")
    new_password = data.get("new_password")
    if not email or not otp or not new_password:
        raise HTTPException(status_code=400, detail="Invalid request")
    user = user_repo.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from app.services.password_reset import verify_and_consume_otp
    if not verify_and_consume_otp(email, otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    user_repo.update_user(db, user, UserUpdate(password=new_password))
    logger.info("Password reset for %s", email)
    return success({"detail": "password updated"}).dict()


@router.post("/request-verify", response_model=StandardResponse, summary="Request email verification")
def request_verification(data: dict, db: Session = Depends(get_db)) -> dict:
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    check_otp_rate_limit(f"verify:{email}")
    user = user_repo.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    otp = generate_verification_token(email)
    logger.info("Verification requested for %s", email)
    return success({"otp": otp}).dict()


@router.post("/verify-email", response_model=StandardResponse, summary="Verify email")
def verify_email(data: dict, db: Session = Depends(get_db)) -> dict:
    email = data.get("email")
    otp = data.get("otp")
    if not email or not otp:
        raise HTTPException(status_code=400, detail="Invalid request")
    user = user_repo.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_email_token(email, otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    user_repo.update_user(
        db,
        user,
        UserUpdate(is_verified=True, verified_at=datetime.utcnow()),
    )
    logger.info("Email verified for %s", email)
    return success({"detail": "email verified"}).dict()
