from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminStatsOut(BaseModel):
    total_users: int
    total_students: int
    total_instructors: int
    total_courses: int
    published_courses: int
    total_enrollments: int
    gross_revenue: float
    net_instructor_payout: float
    active_languages: int


class AdminUserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    enrolled_courses_count: int = 0
    courses_taught_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminUsersListOut(BaseModel):
    total: int
    page: int
    limit: int
    users: List[AdminUserOut]


class UserRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(student|instructor|admin)$")


class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None

