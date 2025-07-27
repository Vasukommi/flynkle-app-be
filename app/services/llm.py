import logging
import os
from typing import Any
from openai import OpenAI, OpenAIError

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)


def chat_with_openai(message: str) -> str:
    """Send a prompt to OpenAI GPT-4 and return the response."""
    try:
        response: Any = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Flynkle, a witty, deeply personal AI assistant who speaks like a friend and doesn't say 'As an AI...'"},
                {"role": "user", "content": message},
            ],
        )
        return response.choices[0].message.content
    except OpenAIError as exc:  # pragma: no cover - API errors
        logger.exception("OpenAI API request failed")
        raise RuntimeError("OpenAI API request failed") from exc
