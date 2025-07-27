"""Service wrappers for the language model provider."""

import logging
from typing import Any, List, Dict

from openai import OpenAI, OpenAIError

from app.core import settings

openai_client = OpenAI(api_key=settings.openai_api_key)
logger = logging.getLogger(__name__)


def chat_with_openai(message: str) -> tuple[str, int]:
    """Send a prompt to OpenAI GPT-4 and return the response and token usage."""

    try:
        response: Any = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Flynkle, a witty, deeply personal AI assistant who speaks "
                        "like a friend and doesn't say 'As an AI...'"
                    ),
                },
                {"role": "user", "content": message},
            ],
        )
        tokens = 0
        try:
            tokens = int(response.usage.total_tokens)
        except Exception:  # pragma: no cover - optional
            tokens = 0
        return response.choices[0].message.content, tokens
    except OpenAIError as exc:  # pragma: no cover - API errors
        logger.exception("OpenAI API request failed")
        raise RuntimeError("OpenAI API request failed") from exc


def chat_with_openai_history(messages: List[Dict[str, str]]) -> tuple[str, int]:
    """Send conversation history to OpenAI GPT-4."""
    try:
        response: Any = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
        )
        tokens = 0
        try:
            tokens = int(response.usage.total_tokens)
        except Exception:  # pragma: no cover - optional
            tokens = 0
        return response.choices[0].message.content, tokens
    except OpenAIError as exc:  # pragma: no cover - API errors
        logger.exception("OpenAI API request failed")
        raise RuntimeError(str(exc)) from exc
