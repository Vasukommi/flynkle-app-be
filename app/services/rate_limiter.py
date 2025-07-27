"""Simple in-memory rate limiting utilities."""

import time
from collections import deque, defaultdict
from uuid import UUID

from fastapi import HTTPException

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_COUNT = 5

_chat_log: dict[UUID, deque[float]] = defaultdict(deque)
_login_log: dict[str, deque[float]] = defaultdict(deque)


def _prune(q: deque[float]) -> None:
    now = time.time()
    while q and now - q[0] > RATE_LIMIT_WINDOW:
        q.popleft()


def check_chat_rate_limit(user_id: UUID) -> None:
    """Limit chat requests per user per time window."""
    q = _chat_log[user_id]
    _prune(q)
    if len(q) >= RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail="Too many requests")
    q.append(time.time())


def check_login_rate_limit(identifier: str) -> None:
    """Limit login attempts per identifier (usually email)."""
    q = _login_log[identifier]
    _prune(q)
    if len(q) >= RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    q.append(time.time())
