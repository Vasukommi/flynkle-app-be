from uuid import UUID
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import user as user_repo
from app.core import decode_access_token


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
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        user_id = x_user_id
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing credentials")

    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def verify_admin(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user
