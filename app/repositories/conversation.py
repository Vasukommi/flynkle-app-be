from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.conversation import Conversation


def create_conversation(db: Session, user_id: UUID, title: Optional[str] = None) -> Conversation:
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db: Session, conversation_id: UUID) -> Optional[Conversation]:
    return db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()


def list_conversations(db: Session, user_id: UUID) -> List[Conversation]:
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).all()


def count_conversations(db: Session, user_id: UUID) -> int:
    """Return number of conversations owned by the user."""
    return db.query(Conversation).filter(Conversation.user_id == user_id).count()


def update_conversation(db: Session, conv: Conversation, title: Optional[str] = None, status: Optional[str] = None) -> Conversation:
    if title is not None:
        conv.title = title
    if status is not None:
        conv.status = status
    db.commit()
    db.refresh(conv)
    return conv


def delete_conversation(db: Session, conv: Conversation) -> Conversation:
    db.delete(conv)
    db.commit()
    return conv
