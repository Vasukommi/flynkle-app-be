import logging

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import chat_with_openai

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse, summary="Chat with OpenAI GPT-4")
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        response = await run_in_threadpool(chat_with_openai, request.message)
        return ChatResponse(response=response)
    except Exception as exc:  # pragma: no cover - simple catch
        logger.exception("LLM request failed")
        raise HTTPException(status_code=500, detail="LLM request failed") from exc
