from datetime import date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class UsageRead(BaseModel):
    usage_id: UUID
    user_id: UUID
    date: date
    message_count: int
    token_count: Optional[int] = None
    file_uploads: Optional[int] = None

    class Config:
        orm_mode = True
