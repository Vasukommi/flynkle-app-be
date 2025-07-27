from uuid import UUID
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import user as user_repo


def get_current_user(
    user_id: UUID = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db),
):
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def verify_admin(admin: str = Header(None, alias="X-Admin")):
    if admin != "true":
        raise HTTPException(status_code=403, detail="Admin privileges required")
