from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.repositories import user as user_repo
from app.schemas import UserCreate, UserRead, UserUpdate
from app.core import success, StandardResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=StandardResponse, summary="Create user")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    try:
        user = user_repo.create_user(db, user_in)
        return success(UserRead.model_validate(user)).dict()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")


@router.get("/{user_id}", response_model=StandardResponse, summary="Get user")
def get_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return success(UserRead.model_validate(user)).dict()


@router.get("", response_model=StandardResponse, summary="List users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[UserRead]:
    users = user_repo.list_users(db, skip=skip, limit=limit, search=search)
    payload = [UserRead.model_validate(u) for u in users]
    return success(payload).dict()


@router.put("/{user_id}", response_model=StandardResponse, summary="Update user")
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated = user_repo.update_user(db, user, user_in)
    return success(UserRead.model_validate(updated)).dict()


@router.delete("/{user_id}", response_model=StandardResponse, summary="Delete user")
def delete_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    deleted = user_repo.delete_user(db, user)
    return success(UserRead.model_validate(deleted)).dict()

from app.api.deps import get_current_user

@router.get("/me", response_model=StandardResponse, summary="Get current user")
def read_me(current_user = Depends(get_current_user)) -> UserRead:
    return success(UserRead.model_validate(current_user)).dict()

@router.patch("/me", response_model=StandardResponse, summary="Update current user")
def update_me(
    user_in: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    updated = user_repo.update_user(db, current_user, user_in)
    return success(UserRead.model_validate(updated)).dict()

@router.delete("/me", response_model=StandardResponse, summary="Delete current user")
def delete_me(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    deleted = user_repo.delete_user(db, current_user)
    return success(UserRead.model_validate(deleted)).dict()
