from datetime import datetime, timedelta
from uuid import UUID

import jwt
from typing import Set
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_revoked_tokens: Set[str] = set()


def revoke_token(token: str) -> None:
    """Mark a token as revoked."""
    _revoked_tokens.add(token)


def is_token_revoked(token: str) -> bool:
    """Check whether the given token has been revoked."""
    return token in _revoked_tokens

def hash_password(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against the hash."""
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: UUID) -> str:
    """Generate a JWT access token for the given user."""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token


def decode_access_token(token: str) -> UUID:
    """Decode a JWT and return the user id."""
    if is_token_revoked(token):
        raise jwt.InvalidTokenError("Token revoked")
    data = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    return UUID(data["sub"])
