# app/db/base.py
from app.models.user import User  # include all future models here
from app.db.database import Base

# This file ensures all models are registered for Alembic
__all__ = ["User"]
