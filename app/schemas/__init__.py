from .chat import ChatRequest, ChatResponse
from .user import UserCreate, UserRead, UserUpdate
from .conversation import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    ConversationSummary,
)
from .message import MessageCreate, MessageRead, MessageUpdate
from .usage import UsageRead
from .upload import UploadRead
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "ConversationCreate",
    "ConversationRead",
    "ConversationUpdate",
    "ConversationSummary",
    "MessageCreate",
    "MessageRead",
    "MessageUpdate",
    "UsageRead",
    "UploadRead",
    "LoginRequest",
    "TokenResponse",
]
