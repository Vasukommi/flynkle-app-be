"""Simple in-memory rate limiting utilities."""

import time
from collections import deque, defaultdict
from uuid import UUID

from fastapi import HTTPException

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_COUNT = 5

_request_log: dict[UUID, deque[float]] = defaultdict(deque)


def check_chat_rate_limit(user_id: UUID) -> None:
    """Limit chat requests per user per time window."""
    now = time.time()
    q = _request_log[user_id]
    while q and now - q[0] > RATE_LIMIT_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT_COUNT:
        raise HTTPException(status_code=429, detail="Too many requests")
    q.append(now)
