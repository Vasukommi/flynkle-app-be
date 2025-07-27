from typing import Optional
from uuid import UUID

from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    provider: Optional[str] = None
    provider_id: Optional[str] = None
    is_verified: Optional[bool] = False
    verified_at: Optional[datetime] = None
    profile: Optional[dict] = None
    is_active: Optional[bool] = True
    is_suspended: Optional[bool] = False
    plan: Optional[str] = "free"


class UserCreate(UserBase):
    provider: str
    password: str


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserRead(UserBase):
    user_id: UUID
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
