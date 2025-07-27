from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user
from app.db.database import get_db
from app.repositories import conversation as convo_repo
from app.repositories import message as message_repo
from app.repositories import usage as usage_repo
from app.repositories import user as user_repo
from app.schemas import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
    MessageRead,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationRead], summary="List conversations")
def list_conversations(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ConversationRead]:
    return convo_repo.list_conversations(db, current_user.user_id)


@router.post("", response_model=ConversationRead, summary="Create conversation")
def create_conversation(
    convo_in: ConversationCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    return convo_repo.create_conversation(db, current_user.user_id, convo_in.title)


@router.get("/{conversation_id}", response_model=ConversationRead, summary="Get conversation")
def get_conversation(
    conversation_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo


@router.patch("/{conversation_id}", response_model=ConversationRead, summary="Update conversation")
def update_conversation(
    conversation_id: UUID,
    convo_in: ConversationUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo_repo.update_conversation(db, convo, convo_in.title, convo_in.status)


@router.delete("/{conversation_id}", response_model=ConversationRead, summary="Delete conversation")
def delete_conversation(
    conversation_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo_repo.delete_conversation(db, convo)


@router.get("/{conversation_id}/messages", response_model=List[MessageRead], summary="List messages")
def list_messages(
    conversation_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[MessageRead]:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return message_repo.list_messages(db, conversation_id, skip=skip, limit=limit)


@router.post("/{conversation_id}/messages", response_model=MessageRead, summary="Create message")
def create_message(
    conversation_id: UUID,
    msg_in: MessageCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # plan enforcement
    if current_user.plan == "free":
        daily = usage_repo.get_daily_usage(db, current_user.user_id, date.today())
        if daily and daily.message_count >= 20:
            raise HTTPException(status_code=403, detail="Upgrade required")
    msg = message_repo.create_message(
        db,
        conversation_id,
        current_user.user_id,
        msg_in.content,
        msg_in.message_type,
    )
    usage_repo.increment_message_count(db, current_user.user_id, date.today())
    return msg


@router.get("/messages/{message_id}", response_model=MessageRead, summary="Get message")
def get_message(
    message_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    msg = message_repo.get_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    convo = convo_repo.get_conversation(db, msg.conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


@router.delete("/messages/{message_id}", response_model=MessageRead, summary="Delete message")
def delete_message(
    message_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    msg = message_repo.get_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    convo = convo_repo.get_conversation(db, msg.conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Message not found")
    return message_repo.delete_message(db, msg)
