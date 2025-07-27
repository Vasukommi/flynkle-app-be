import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.core import success, StandardResponse
from app.db.database import get_db
from app.schemas.chat import ChatRequest
from app.services.llm import chat_with_openai
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
    # plan enforcement
    if current_user.plan == "free":
        daily = usage_repo.get_daily_usage(db, current_user.user_id, date.today())
        if daily and daily.message_count >= 20:
            raise HTTPException(status_code=403, detail="Upgrade required")
    try:
        response = await run_in_threadpool(chat_with_openai, request.message)
    except Exception as exc:  # pragma: no cover - simple catch
        logger.exception("LLM request failed")
        raise HTTPException(status_code=500, detail="LLM request failed") from exc
    usage_repo.increment_message_count(db, current_user.user_id, date.today())
    return success({"response": response}).dict()
