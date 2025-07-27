from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password


def create_user(db: Session, user_in: UserCreate) -> User:
    data = user_in.dict(exclude_unset=True)
    password = data.pop("password")
    user = User(**data, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve a user by email."""
    return db.query(User).filter(User.email == email).first()


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


def delete_user(db: Session, user: User) -> User:
    db.delete(user)
    db.commit()
    return user


def list_users(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[User]:
    query = db.query(User)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(User.email.ilike(pattern), User.phone_number.ilike(pattern)))
    return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
