from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password
from datetime import datetime


def create_user(db: Session, user_in: UserCreate) -> User:
    data = user_in.dict(exclude_unset=True)
    password = data.pop("password")
    user = User(**data, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    return (
        db.query(User)
        .filter(User.user_id == user_id, User.deleted_at.is_(None))
        .first()
    )


def get_user_include_deleted(db: Session, user_id: UUID) -> Optional[User]:
    """Return a user regardless of deletion state."""
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve a user by email."""
    return (
        db.query(User)
        .filter(User.email == email, User.deleted_at.is_(None))
        .first()
    )


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    update_data = user_in.dict(exclude_unset=True)
    password = update_data.pop("password", None)
    for field, value in update_data.items():
        setattr(user, field, value)
    if password:
        user.password = hash_password(password)
    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user: User) -> None:
    """Record the user's last login timestamp."""
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)


def delete_user(db: Session, user: User) -> User:
    user.is_active = False
    user.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def suspend_user(db: Session, user: User) -> User:
    """Suspend a user account."""
    user.is_suspended = True
    db.commit()
    db.refresh(user)
    return user


def reinstate_user(db: Session, user: User) -> User:
    """Reinstate a suspended user."""
    user.is_suspended = False
    db.commit()
    db.refresh(user)
    return user


def restore_user(db: Session, user: User) -> User:
    """Restore a soft-deleted user."""
    user.is_active = True
    user.deleted_at = None
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[User]:
    query = db.query(User).filter(User.deleted_at.is_(None))
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(User.email.ilike(pattern), User.phone_number.ilike(pattern)))
    return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
