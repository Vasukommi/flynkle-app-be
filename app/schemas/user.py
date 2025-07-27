from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    provider: Optional[str] = None
    provider_id: Optional[str] = None
    is_verified: Optional[bool] = False
    profile: Optional[dict] = None
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False


class UserCreate(UserBase):
    provider: str


class UserUpdate(UserBase):
    pass


class UserRead(UserBase):
    user_id: UUID

    class Config:
        orm_mode = True
