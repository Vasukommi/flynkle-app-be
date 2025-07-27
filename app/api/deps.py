from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import user as user_repo
from app.core import decode_access_token


def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db),
):
    token = authorization.replace("Bearer ", "")
    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def verify_admin(admin: str = Header(None, alias="X-Admin")):
    if admin != "true":
        raise HTTPException(status_code=403, detail="Admin privileges required")
