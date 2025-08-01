from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    chat,
    users,
    auth,
    plans,
    conversations,
    message_router,
    uploads,
    admin,
    moderation,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(users.router)
api_router.include_router(auth.router)
api_router.include_router(plans.router)
api_router.include_router(conversations.router)
api_router.include_router(message_router)
api_router.include_router(uploads.router)
api_router.include_router(admin.router)
api_router.include_router(moderation.router)
