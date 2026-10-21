from typing import Optional
from pydantic import BaseModel, EmailStr
from app.schemas.user import UserOut


class SSOExchangeRequest(BaseModel):
    code: str


class DevLoginRequest(BaseModel):
    email: EmailStr
    role: str = "student"  # 'student' | 'instructor' | 'admin'
    full_name: Optional[str] = "Dev Tester"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
