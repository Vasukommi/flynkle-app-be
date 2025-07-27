from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import verify_admin
from app.db.database import get_db
from app.repositories import user as user_repo
from app.schemas import UserRead, UserUpdate
from app.core import success, StandardResponse

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_admin)])


@router.get("/users", response_model=StandardResponse, summary="List users (admin)")
def admin_list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[UserRead]:
    users = user_repo.list_users(db, skip=skip, limit=limit, search=search)
    payload = [UserRead.model_validate(u) for u in users]
    return success(payload).dict()


@router.patch("/users/{user_id}", response_model=StandardResponse, summary="Update user (admin)")
def admin_update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated = user_repo.update_user(db, user, user_in)
    return success(UserRead.model_validate(updated)).dict()
