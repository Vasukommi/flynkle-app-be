import logging
import os
from typing import Any
import openai
from openai.error import OpenAIError

openai.api_key = os.getenv("OPENAI_API_KEY")
logger = logging.getLogger(__name__)


def chat_with_openai(message: str) -> str:
    """Send a prompt to OpenAI GPT-4 and return the response."""
    try:
        response: Any = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": message}],
        )
        return response["choices"][0]["message"]["content"]
    except OpenAIError as exc:  # pragma: no cover - API errors
        logger.exception("OpenAI API request failed")
        raise RuntimeError("OpenAI API request failed") from exc
