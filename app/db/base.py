# app/db/base.py
from app.models import User, Conversation, Message, Usage  # include all models here
from app.db.database import Base

# This file ensures all models are registered for Alembic
__all__ = ["User", "Conversation", "Message", "Usage"]
