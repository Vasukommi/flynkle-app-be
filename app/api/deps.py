from uuid import UUID
import logging
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import user as user_repo
from app.core import decode_access_token


logger = logging.getLogger(__name__)


def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    x_user_id: UUID | None = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    if authorization:
        token = authorization.replace("Bearer ", "")
        try:
            user_id = decode_access_token(token)
        except Exception:
            logger.warning("Invalid token used")
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        user_id = x_user_id
    if not user_id:
        logger.warning("Missing credentials")
        raise HTTPException(status_code=401, detail="Missing credentials")

    user = user_repo.get_user(db, user_id)
    if not user:
        logger.warning("User %s not found", user_id)
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active or user.is_suspended:
        logger.warning("Inactive or suspended user %s", user.user_id)
        raise HTTPException(status_code=403, detail="Account disabled")
    return user


def verify_admin(current_user=Depends(get_current_user)):
    """Ensure the authenticated user has admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
