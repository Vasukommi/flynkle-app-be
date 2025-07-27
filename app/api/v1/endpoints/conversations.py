from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user
from app.core import success
from app.db.database import get_db
from app.repositories import conversation as convo_repo
from app.repositories import message as message_repo
from app.repositories import usage as usage_repo
from app.repositories import user as user_repo
from app.api.v1.endpoints.plans import PLANS
from app.schemas import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    MessageUpdate,
    MessageCreate,
    MessageRead,
)
from app.core import success, StandardResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])
message_router = APIRouter(prefix="/messages", tags=["conversations"])


@router.get("", response_model=StandardResponse, summary="List conversations")
def list_conversations(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ConversationRead]:
    convos = convo_repo.list_conversations(db, current_user.user_id)
    payload = [ConversationRead.model_validate(c) for c in convos]
    return success(payload).dict()


@router.post("", response_model=StandardResponse, summary="Create conversation")
def create_conversation(
    convo_in: ConversationCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    conv = convo_repo.create_conversation(db, current_user.user_id, convo_in.title)
    return success(ConversationRead.model_validate(conv)).dict()


@router.get("/{conversation_id}", response_model=StandardResponse, summary="Get conversation")
def get_conversation(
    conversation_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return success(ConversationRead.model_validate(convo)).dict()


@router.patch("/{conversation_id}", response_model=StandardResponse, summary="Update conversation")
def update_conversation(
    conversation_id: UUID,
    convo_in: ConversationUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    updated = convo_repo.update_conversation(db, convo, convo_in.title, convo_in.status)
    return success(ConversationRead.model_validate(updated)).dict()


@router.delete("/{conversation_id}", response_model=StandardResponse, summary="Delete conversation")
def delete_conversation(
    conversation_id: UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    deleted = convo_repo.delete_conversation(db, convo)
    return success(ConversationRead.model_validate(deleted)).dict()


@router.get("/{conversation_id}/messages", response_model=StandardResponse, summary="List messages")
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
    msgs = message_repo.list_messages(db, conversation_id, skip=skip, limit=limit)
    payload = [MessageRead.model_validate(m) for m in msgs]
    return success(payload).dict()


@router.post("/{conversation_id}/messages", response_model=StandardResponse, summary="Create message")
def create_message(
    conversation_id: UUID,
    msg_in: MessageCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # plan enforcement using configured plans
    plan = PLANS.get(current_user.plan, PLANS["free"])
    daily = usage_repo.get_daily_usage(db, current_user.user_id, date.today())
    if daily and daily.message_count >= plan["daily_messages"]:
        raise HTTPException(status_code=403, detail="Upgrade required")
    msg = message_repo.create_message(
        db,
        conversation_id,
        current_user.user_id,
        msg_in.content,
        msg_in.message_type,
    )
    usage_repo.increment_message_count(db, current_user.user_id, date.today())
    return success(MessageRead.model_validate(msg)).dict()


@message_router.get("/{message_id}", response_model=StandardResponse, summary="Get message")
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
    return success(MessageRead.model_validate(msg)).dict()


@message_router.patch("/{message_id}", response_model=StandardResponse, summary="Update message")
def update_message(
    message_id: UUID,
    msg_in: MessageUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    msg = message_repo.get_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    convo = convo_repo.get_conversation(db, msg.conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Message not found")
    updated = message_repo.update_message(
        db,
        msg,
        content=msg_in.content,
        message_type=msg_in.message_type,
        extra=msg_in.extra,
    )
    return success(MessageRead.model_validate(updated)).dict()


@message_router.delete("/{message_id}", response_model=StandardResponse, summary="Delete message")
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
    deleted = message_repo.delete_message(db, msg)
    return success(MessageRead.model_validate(deleted)).dict()
