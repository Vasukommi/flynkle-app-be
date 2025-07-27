from datetime import datetime, timedelta
from uuid import UUID

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    data = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    return UUID(data["sub"])
