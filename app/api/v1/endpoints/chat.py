import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask
from starlette.concurrency import iterate_in_threadpool

from app.core import success, StandardResponse
from app.db.database import get_db
from app.schemas.chat import ChatRequest
from app.services.llm import chat_with_openai_history, stream_openai_history
from app.services import check_chat_rate_limit
from app.core import PLANS
from app.repositories import usage as usage_repo
from app.repositories import conversation as convo_repo
from app.repositories import message as message_repo
from app.api.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=StandardResponse, summary="Chat with OpenAI GPT-4")
async def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db=Depends(get_db),
    stream: bool = False,
) -> dict | StreamingResponse:
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

    history = [
        {
            "role": "system",
            "content": (
                "You are Flynkle, a witty, deeply personal AI assistant who speaks "
                "like a friend and doesn't say 'As an AI...'"
            ),
        }
    ]
    if request.conversation_id:
        convo = convo_repo.get_conversation(db, request.conversation_id)
        if not convo or convo.user_id != current_user.user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        msgs = message_repo.list_messages(db, request.conversation_id)
        for m in msgs:
            if m.message_type == "user":
                role = "user"
            elif m.message_type == "ai":
                role = "assistant"
            else:
                continue
            text = m.content.get("text") if isinstance(m.content, dict) else str(m.content)
            history.append({"role": role, "content": text})
    history.append({"role": "user", "content": request.message})

    if stream:
        state: dict[str, Any] = {}
        def finalize() -> None:
            if request.conversation_id:
                message_repo.create_message(
                    db,
                    request.conversation_id,
                    current_user.user_id,
                    {"text": request.message},
                    "user",
                )
                message_repo.create_message(
                    db,
                    request.conversation_id,
                    None,
                    {"text": state.get("response", "")},
                    "ai",
                )
            usage_repo.increment_message_count(db, current_user.user_id, date.today())
            usage_repo.increment_token_count(db, current_user.user_id, date.today(), state.get("tokens", 0))

        try:
            generator = stream_openai_history(history, state)
            return StreamingResponse(
                iterate_in_threadpool(generator),
                background=BackgroundTask(finalize),
                media_type="text/plain",
            )
        except RuntimeError as exc:
            logger.exception("LLM request failed")
            raise HTTPException(
                status_code=502,
                detail={"message": "OpenAI request failed", "data": {"source": "openai", "reason": str(exc)}},
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected errors
            logger.exception("Unexpected chat failure")
            raise HTTPException(
                status_code=500,
                detail={"message": "Internal error", "data": {"source": "server", "reason": "unexpected"}},
            ) from exc
    else:
        try:
            content, tokens = await run_in_threadpool(chat_with_openai_history, history)
        except RuntimeError as exc:  # pragma: no cover - LLM errors
            logger.exception("LLM request failed")
            raise HTTPException(
                status_code=502,
                detail={"message": "OpenAI request failed", "data": {"source": "openai", "reason": str(exc)}},
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected errors
            logger.exception("Unexpected chat failure")
            raise HTTPException(
                status_code=500,
                detail={"message": "Internal error", "data": {"source": "server", "reason": "unexpected"}},
            ) from exc

        if request.conversation_id:
            message_repo.create_message(
                db,
                request.conversation_id,
                current_user.user_id,
                {"text": request.message},
                "user",
            )
            message_repo.create_message(
                db,
                request.conversation_id,
                None,
                {"text": content},
                "ai",
            )
        usage_repo.increment_message_count(db, current_user.user_id, date.today())
        usage_repo.increment_token_count(db, current_user.user_id, date.today(), tokens)
        return success({"response": content, "tokens": tokens}).dict()
