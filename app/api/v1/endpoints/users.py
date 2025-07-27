from typing import List, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.repositories import user as user_repo
from app.schemas import UserCreate, UserRead, UserUpdate
from app.core import success, StandardResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@router.post("", response_model=StandardResponse, summary="Create user")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    try:
        user = user_repo.create_user(db, user_in)
        logger.info("Created user %s", user.user_id)
        return success(UserRead.model_validate(user)).dict()
    except IntegrityError:
        db.rollback()
        logger.warning("Duplicate user %s", user_in.email)
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
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.user_id != user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = user_repo.update_user(db, user, user_in)
    logger.info("User %s updated by %s", user.user_id, current_user.user_id)
    return success(UserRead.model_validate(updated)).dict()


@router.patch("/{user_id}", response_model=StandardResponse, summary="Partial update user")
def patch_user(
    user_id: UUID,
    user_in: UserUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.user_id != user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = user_repo.update_user(db, user, user_in)
    logger.info("User %s patched by %s", user.user_id, current_user.user_id)
    return success(UserRead.model_validate(updated)).dict()


@router.delete("/{user_id}", response_model=StandardResponse, summary="Delete user")
def delete_user(
    user_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.user_id != user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    deleted = user_repo.delete_user(db, user)
    logger.info("User %s deleted by %s", user.user_id, current_user.user_id)
    return success(UserRead.model_validate(deleted)).dict()

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
    logger.info("User %s updated self", current_user.user_id)
    return success(UserRead.model_validate(updated)).dict()

@router.delete("/me", response_model=StandardResponse, summary="Delete current user")
def delete_me(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    deleted = user_repo.delete_user(db, current_user)
    logger.info("User %s deleted self", current_user.user_id)
    return success(UserRead.model_validate(deleted)).dict()
