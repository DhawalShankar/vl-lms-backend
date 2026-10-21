from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "student"
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    vartalang_user_id: Optional[str] = None


class UserOut(UserBase):
    id: UUID
    vartalang_user_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
