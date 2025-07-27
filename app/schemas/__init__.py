from .chat import ChatRequest, ChatResponse
from .user import UserCreate, UserRead, UserUpdate
from .conversation import ConversationCreate, ConversationRead, ConversationUpdate
from .message import MessageCreate, MessageRead
from .usage import UsageRead
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "ConversationCreate",
    "ConversationRead",
    "ConversationUpdate",
    "MessageCreate",
    "MessageRead",
    "UsageRead",
    "LoginRequest",
    "TokenResponse",
]
