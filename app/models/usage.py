import uuid
from sqlalchemy import Column, Date, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.database import Base


class Usage(Base):
    __tablename__ = "usage"

    usage_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    message_count = Column(Integer, nullable=False, default=0)
    token_count = Column(Integer, nullable=True)
    file_uploads = Column(Integer, nullable=True)
    last_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
