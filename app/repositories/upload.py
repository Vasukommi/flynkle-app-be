from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.upload import Upload


def create_upload(db: Session, user_id: UUID, bucket: str, key: str, content_type: str | None, size: int) -> Upload:
    upload = Upload(
        user_id=user_id,
        bucket=bucket,
        key=key,
        content_type=content_type,
        size=size,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def list_uploads(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Upload]:
    return (
        db.query(Upload)
        .filter(Upload.user_id == user_id)
        .order_by(Upload.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_upload(db: Session, upload_id: UUID) -> Optional[Upload]:
    return db.query(Upload).filter(Upload.upload_id == upload_id).first()


def delete_upload(db: Session, upload: Upload) -> Upload:
    db.delete(upload)
    db.commit()
    return upload
