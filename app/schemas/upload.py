from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UploadRead(BaseModel):
    upload_id: UUID
    bucket: str
    key: str
    content_type: Optional[str] = None
    size: int
    created_at: Optional[datetime] = None
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
