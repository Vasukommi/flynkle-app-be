from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class MessageBase(BaseModel):
    content: dict
    message_type: str

class MessageCreate(MessageBase):
    invoke_llm: bool = False

class MessageUpdate(BaseModel):
    content: Optional[dict] = None
    message_type: Optional[str] = None
    extra: Optional[dict] = None

class MessageRead(MessageBase):
    message_id: UUID
    conversation_id: UUID
    user_id: Optional[UUID] = None
    timestamp: Optional[datetime] = None
    extra: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)
