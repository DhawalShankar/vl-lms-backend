"""Pydantic Request and Response Schemas."""

from app.schemas.user import UserBase, UserCreate, UserOut
from app.schemas.auth import SSOExchangeRequest, DevLoginRequest, TokenResponse
from app.schemas.course import (
    InstructorPublic,
    LanguageSummary,
    InstructorLanguageSummary,
    LessonCreate,
    LessonUpdate,
    LessonOut,
    ModuleCreate,
    ModuleUpdate,
    ModuleOut,
    CourseCreate,
    CourseUpdate,
    CourseStatusUpdate,
    CourseOut,
    CourseDetailOut,
)
from app.schemas.enrollment import (
    EnrollmentOut,
    LessonProgressToggleResponse,
    CourseProgressDetail,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserOut",
    "SSOExchangeRequest",
    "DevLoginRequest",
    "TokenResponse",
    "InstructorPublic",
    "LanguageSummary",
    "InstructorLanguageSummary",
    "LessonCreate",
    "LessonUpdate",
    "LessonOut",
    "ModuleCreate",
    "ModuleUpdate",
    "ModuleOut",
    "CourseCreate",
    "CourseUpdate",
    "CourseStatusUpdate",
    "CourseOut",
    "CourseDetailOut",
    "EnrollmentOut",
    "LessonProgressToggleResponse",
    "CourseProgressDetail",
]
