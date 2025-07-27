from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_current_user
from app.core import success
from app.db.database import get_db
from app.repositories import conversation as convo_repo
from app.repositories import message as message_repo
from app.repositories import usage as usage_repo
from app.core import PLANS
from app.services.llm import chat_with_openai
from app.services import check_chat_rate_limit, check_message_rate_limit
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
logger = logging.getLogger(__name__)


@router.get("", response_model=StandardResponse, summary="List conversations")
def list_conversations(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str | None = None,
) -> List[ConversationRead]:
    convos = convo_repo.list_conversations(db, current_user.user_id, query=q)
    logger.info("Listing conversations for %s", current_user.user_id)
    payload = [ConversationRead.model_validate(c) for c in convos]
    return success(payload).dict()


@router.post("", response_model=StandardResponse, summary="Create conversation")
def create_conversation(
    convo_in: ConversationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    plan = PLANS.get(current_user.plan, PLANS["free"])
    count = convo_repo.count_conversations(db, current_user.user_id)
    if count >= plan["max_conversations"]:
        logger.info("Conversation limit reached for %s", current_user.user_id)
        raise HTTPException(status_code=403, detail="Upgrade required")
    conv = convo_repo.create_conversation(db, current_user.user_id, convo_in.title)
    logger.info(
        "Conversation %s created for %s", conv.conversation_id, current_user.user_id
    )
    return success(ConversationRead.model_validate(conv)).dict()


@router.get(
    "/{conversation_id}", response_model=StandardResponse, summary="Get conversation"
)
def get_conversation(
    conversation_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return success(ConversationRead.model_validate(convo)).dict()


@router.patch(
    "/{conversation_id}", response_model=StandardResponse, summary="Update conversation"
)
def update_conversation(
    conversation_id: UUID,
    convo_in: ConversationUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    updated = convo_repo.update_conversation(db, convo, convo_in.title, convo_in.status)
    logger.info("Conversation %s updated by %s", conversation_id, current_user.user_id)
    return success(ConversationRead.model_validate(updated)).dict()


@router.delete(
    "/{conversation_id}", response_model=StandardResponse, summary="Delete conversation"
)
def delete_conversation(
    conversation_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    deleted = convo_repo.delete_conversation(db, convo)
    logger.info("Conversation %s deleted by %s", conversation_id, current_user.user_id)
    return success(ConversationRead.model_validate(deleted)).dict()


@router.delete("", response_model=StandardResponse, summary="Bulk delete conversations")
def bulk_delete_conversations(
    ids: List[UUID] = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = convo_repo.bulk_delete(db, current_user.user_id, ids)
    logger.info("Bulk deleted %s conversations for %s", deleted, current_user.user_id)
    return success({"deleted": deleted}).dict()


@router.get(
    "/{conversation_id}/messages",
    response_model=StandardResponse,
    summary="List messages",
)
def list_messages(
    conversation_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[MessageRead]:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = message_repo.list_messages(db, conversation_id, skip=skip, limit=limit)
    logger.info("Listing messages in %s for %s", conversation_id, current_user.user_id)
    payload = [MessageRead.model_validate(m) for m in msgs]
    return success(payload).dict()


@router.post(
    "/{conversation_id}/messages",
    response_model=StandardResponse,
    summary="Create message",
)
def create_message(
    conversation_id: UUID,
    msg_in: MessageCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    convo = convo_repo.get_conversation(db, conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    check_message_rate_limit(current_user.user_id)
    # plan enforcement using configured plans
    plan = PLANS.get(current_user.plan, PLANS["free"])
    daily = usage_repo.get_daily_usage(db, current_user.user_id, date.today())
    if daily and daily.message_count >= plan["daily_messages"]:
        raise HTTPException(status_code=403, detail="Upgrade required")
    if daily and daily.token_count is not None and daily.token_count >= plan["daily_tokens"]:
        raise HTTPException(status_code=403, detail="Upgrade required")
    if msg_in.message_type == "file":
        uploads = daily.file_uploads if daily else 0
        if uploads >= plan.get("max_file_uploads", 0):
            raise HTTPException(status_code=403, detail="Upgrade required")
    msg = message_repo.create_message(
        db,
        conversation_id,
        current_user.user_id,
        msg_in.content,
        msg_in.message_type,
    )
    logger.info(
        "Message %s created in %s by %s",
        msg.message_id,
        conversation_id,
        current_user.user_id,
    )
    usage_repo.increment_message_count(db, current_user.user_id, date.today())
    if msg_in.message_type == "file":
        usage_repo.increment_file_uploads(db, current_user.user_id, date.today())

    if msg_in.invoke_llm and msg_in.message_type == "user":
        check_chat_rate_limit(current_user.user_id)
        tokens_used = daily.token_count or 0 if daily else 0
        if tokens_used >= plan["daily_tokens"]:
            raise HTTPException(status_code=403, detail="Upgrade required")
        try:
            content, tokens = chat_with_openai(str(msg_in.content))
        except Exception as exc:  # pragma: no cover - LLM failure
            logger.exception("LLM call failed")
        else:
            if tokens_used + tokens > plan["daily_tokens"]:
                raise HTTPException(status_code=403, detail="Upgrade required")
            ai_msg = message_repo.create_message(
                db,
                conversation_id,
                None,
                {"text": content},
                "ai",
            )
            usage_repo.increment_token_count(
                db, current_user.user_id, date.today(), tokens
            )
            logger.info(
                "AI message %s created in %s", ai_msg.message_id, conversation_id
            )

    return success(MessageRead.model_validate(msg)).dict()


@message_router.get(
    "/{message_id}", response_model=StandardResponse, summary="Get message"
)
def get_message(
    message_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    msg = message_repo.get_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    convo = convo_repo.get_conversation(db, msg.conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Message not found")
    logger.info("Message %s retrieved by %s", message_id, current_user.user_id)
    return success(MessageRead.model_validate(msg)).dict()


@message_router.patch(
    "/{message_id}", response_model=StandardResponse, summary="Update message"
)
def update_message(
    message_id: UUID,
    msg_in: MessageUpdate,
    current_user=Depends(get_current_user),
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
    logger.info("Message %s updated by %s", message_id, current_user.user_id)
    return success(MessageRead.model_validate(updated)).dict()


@message_router.delete(
    "/{message_id}", response_model=StandardResponse, summary="Delete message"
)
def delete_message(
    message_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageRead:
    msg = message_repo.get_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    convo = convo_repo.get_conversation(db, msg.conversation_id)
    if not convo or convo.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Message not found")
    deleted = message_repo.delete_message(db, msg)
    logger.info("Message %s deleted by %s", message_id, current_user.user_id)
    return success(MessageRead.model_validate(deleted)).dict()
