import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    provider = Column(String, nullable=False)
    provider_id = Column(String, index=True, nullable=True)

    password = Column(String, nullable=True)

    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    plan = Column(String, default="free")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

    deleted_at = Column(DateTime, nullable=True)

    profile = Column(JSON, server_default='{}')

