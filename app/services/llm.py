import os
from typing import Any
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


def chat_with_openai(message: str) -> str:
    """Send a prompt to OpenAI GPT-4 and return the response."""
    response: Any = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message}],
    )
    return response["choices"][0]["message"]["content"]

