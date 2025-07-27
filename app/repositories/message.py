from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.message import Message


def create_message(db: Session, conversation_id: UUID, user_id: Optional[UUID], content: dict, message_type: str) -> Message:
    msg = Message(conversation_id=conversation_id, user_id=user_id, content=content, message_type=message_type)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_message(db: Session, message_id: UUID) -> Optional[Message]:
    return db.query(Message).filter(Message.message_id == message_id).first()


def list_messages(db: Session, conversation_id: UUID, skip: int = 0, limit: int = 100) -> List[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_message(
    db: Session,
    msg: Message,
    content: Optional[dict] = None,
    message_type: Optional[str] = None,
    extra: Optional[dict] = None,
) -> Message:
    if content is not None:
        msg.content = content
    if message_type is not None:
        msg.message_type = message_type
    if extra is not None:
        msg.extra = extra
    db.commit()
    db.refresh(msg)
    return msg


def delete_message(db: Session, msg: Message) -> Message:
    db.delete(msg)
    db.commit()
    return msg
