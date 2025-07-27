from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.repositories import user as user_repo
from app.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, summary="Create user")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    try:
        return user_repo.create_user(db, user_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")


@router.get("/{user_id}", response_model=UserRead, summary="Get user")
def get_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("", response_model=List[UserRead], summary="List users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[UserRead]:
    return user_repo.list_users(db, skip=skip, limit=limit, search=search)


@router.put("/{user_id}", response_model=UserRead, summary="Update user")
def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_repo.update_user(db, user, user_in)


@router.delete("/{user_id}", response_model=UserRead, summary="Delete user")
def delete_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_repo.delete_user(db, user)
