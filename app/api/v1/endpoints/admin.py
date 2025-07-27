from uuid import UUID
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import verify_admin
from app.db.database import get_db
from sqlalchemy.exc import IntegrityError

from app.repositories import user as user_repo
from app.repositories import conversation as convo_repo
from app.repositories import usage as usage_repo
from app.schemas import (
    UserRead,
    UserUpdate,
    UserCreate,
    ConversationRead,
    UsageRead,
)
from app.core import success, StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(verify_admin)]
)


@router.get("/users", response_model=StandardResponse, summary="List users (admin)")
def admin_list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[UserRead]:
    logger.info("Admin listing users")
    users = user_repo.list_users(db, skip=skip, limit=limit, search=search)
    payload = [UserRead.model_validate(u) for u in users]
    return success(payload).dict()


@router.patch(
    "/users/{user_id}", response_model=StandardResponse, summary="Update user (admin)"
)
def admin_update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updated = user_repo.update_user(db, user, user_in)
    logger.info("Admin updated user %s", user_id)
    return success(UserRead.model_validate(updated)).dict()


@router.post("/users", response_model=StandardResponse, summary="Create user (admin)")
def admin_create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    try:
        user = user_repo.create_user(db, user_in)
        logger.info("Admin created user %s", user.user_id)
        return success(UserRead.model_validate(user)).dict()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="User already exists")


@router.delete("/users/{user_id}", response_model=StandardResponse, summary="Delete user (admin)")
def admin_delete_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    deleted = user_repo.delete_user(db, user)
    logger.info("Admin deleted user %s", user_id)
    return success(UserRead.model_validate(deleted)).dict()


@router.get(
    "/users/{user_id}/conversations",
    response_model=StandardResponse,
    summary="User conversations",
)
def admin_user_conversations(
    user_id: UUID, db: Session = Depends(get_db)
) -> List[ConversationRead]:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    convs = convo_repo.list_conversations(db, user_id)
    payload = [ConversationRead.model_validate(c) for c in convs]
    return success(payload).dict()


@router.get(
    "/users/{user_id}/usage",
    response_model=StandardResponse,
    summary="User usage",
)
def admin_user_usage(user_id: UUID, db: Session = Depends(get_db)) -> List[UsageRead]:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    usage = usage_repo.get_usage(db, user_id)
    payload = [UsageRead.model_validate(u) for u in usage]
    return success(payload).dict()


@router.post(
    "/users/{user_id}/suspend",
    response_model=StandardResponse,
    summary="Suspend user",
)
def admin_suspend_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    suspended = user_repo.suspend_user(db, user)
    logger.info("Admin suspended user %s", user_id)
    return success(UserRead.model_validate(suspended)).dict()


@router.post(
    "/users/{user_id}/reinstate",
    response_model=StandardResponse,
    summary="Reinstate user",
)
def admin_reinstate_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = user_repo.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reinstated = user_repo.reinstate_user(db, user)
    logger.info("Admin reinstated user %s", user_id)
    return success(UserRead.model_validate(reinstated)).dict()


@router.post(
    "/users/{user_id}/restore",
    response_model=StandardResponse,
    summary="Restore user",
)
def admin_restore_user(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    """Restore a soft-deleted user."""
    user = user_repo.get_user_include_deleted(db, user_id)
    if not user or user.deleted_at is None:
        raise HTTPException(status_code=404, detail="User not found")
    restored = user_repo.restore_user(db, user)
    logger.info("Admin restored user %s", user_id)
    return success(UserRead.model_validate(restored)).dict()
