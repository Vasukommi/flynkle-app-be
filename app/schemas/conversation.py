from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class ConversationBase(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(ConversationBase):
    pass

class ConversationRead(ConversationBase):
    conversation_id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
