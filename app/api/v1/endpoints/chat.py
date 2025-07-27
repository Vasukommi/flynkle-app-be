import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.core import success, StandardResponse
from app.db.database import get_db
from app.schemas.chat import ChatRequest
from app.services.llm import chat_with_openai
from app.services import check_chat_rate_limit
from app.core import PLANS
from app.repositories import usage as usage_repo
from app.api.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=StandardResponse, summary="Chat with OpenAI GPT-4")
async def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db),
) -> dict:
    """Proxy a message to the language model with plan enforcement."""
    logger.info("Chat request from %s", current_user.user_id)

    # plan enforcement using configured plans
    plan = PLANS.get(current_user.plan, PLANS["free"])
    daily = usage_repo.get_daily_usage(db, current_user.user_id, date.today())
    if daily and daily.message_count >= plan["daily_messages"]:
        raise HTTPException(status_code=403, detail="Upgrade required")
    if daily and daily.token_count is not None and daily.token_count >= plan["daily_tokens"]:
        raise HTTPException(status_code=403, detail="Upgrade required")

    # rate limiting
    check_chat_rate_limit(current_user.user_id)

    try:
        content, tokens = await run_in_threadpool(chat_with_openai, request.message)
    except RuntimeError as exc:  # pragma: no cover - LLM errors
        logger.exception("LLM request failed")
        raise HTTPException(status_code=502, detail="LLM request failed") from exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected chat failure")
        raise HTTPException(status_code=500, detail="Internal error") from exc

    usage_repo.increment_message_count(db, current_user.user_id, date.today())
    usage_repo.increment_token_count(db, current_user.user_id, date.today(), tokens)
    return success({"response": content, "tokens": tokens}).dict()
