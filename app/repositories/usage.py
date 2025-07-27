from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.usage import Usage


def get_usage(db: Session, user_id: UUID) -> List[Usage]:
    return db.query(Usage).filter(Usage.user_id == user_id).order_by(Usage.date.desc()).all()


def get_daily_usage(db: Session, user_id: UUID, day: date) -> Optional[Usage]:
    return db.query(Usage).filter(Usage.user_id == user_id, Usage.date == day).first()


def increment_message_count(db: Session, user_id: UUID, day: date) -> Usage:
    usage = get_daily_usage(db, user_id, day)
    if not usage:
        usage = Usage(user_id=user_id, date=day, message_count=0)
        db.add(usage)
    usage.message_count += 1
    db.commit()
    db.refresh(usage)
    return usage
