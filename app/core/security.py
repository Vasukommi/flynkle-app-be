from datetime import datetime, timedelta
from uuid import UUID
import time

import jwt
import redis
from typing import Set, Dict
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_revoked_tokens: Set[str] = set()
_refresh_tokens: Dict[str, float] = {}

redis_client = None
if hasattr(settings, "redis_url") and settings.redis_url:
    try:
        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        # test connection
        redis_client.ping()
    except Exception:
        redis_client = None


def revoke_token(token: str, expires: int) -> None:
    """Mark a token as revoked."""
    global redis_client
    if redis_client:
        try:
            redis_client.setex(f"revoked:{token}", expires, "1")
            return
        except Exception:
            redis_client = None
    _revoked_tokens.add(token)


def is_token_revoked(token: str) -> bool:
    """Check whether the given token has been revoked."""
    if redis_client:
        return redis_client.exists(f"revoked:{token}") == 1
    return token in _revoked_tokens


def create_refresh_token(user_id: UUID) -> str:
    """Generate a refresh token and store it."""
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    ttl = int((expire - datetime.utcnow()).total_seconds())
    global redis_client
    if redis_client:
        try:
            redis_client.setex(f"refresh:{token}", ttl, str(user_id))
        except Exception:
            redis_client = None
            _refresh_tokens[token] = time.time() + ttl
    else:
        _refresh_tokens[token] = time.time() + ttl
    return token


def revoke_refresh_token(token: str) -> None:
    global redis_client
    if redis_client:
        try:
            redis_client.delete(f"refresh:{token}")
            return
        except Exception:
            redis_client = None
    _refresh_tokens.pop(token, None)


def decode_refresh_token(token: str) -> UUID:
    global redis_client
    if redis_client:
        try:
            exists = redis_client.exists(f"refresh:{token}") == 1
        except Exception:
            redis_client = None
            expires_at = _refresh_tokens.get(token)
            exists = expires_at and expires_at > time.time()
    else:
        expires_at = _refresh_tokens.get(token)
        exists = expires_at and expires_at > time.time()
    if not exists:
        raise jwt.InvalidTokenError("Token revoked")
    data = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    return UUID(data["sub"])

def hash_password(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against the hash."""
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    """Generate a JWT access token for the given user."""
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> UUID:
    """Decode a JWT and return the user id."""
    if is_token_revoked(token):
        raise jwt.InvalidTokenError("Token revoked")
    data = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if data.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    return UUID(data["sub"])
