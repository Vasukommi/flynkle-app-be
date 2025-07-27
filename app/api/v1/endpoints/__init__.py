from .auth import router as auth_router
from .chat import router as chat_router
from .health import router as health_router
from .users import router as users_router
from .plans import router as plans_router
from .conversations import router as conversations_router, message_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "chat_router",
    "health_router",
    "users_router",
    "plans_router",
    "conversations_router",
    "message_router",
    "admin_router",
]
