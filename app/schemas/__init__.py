"""Pydantic Request and Response Schemas."""

from app.schemas.user import UserBase, UserCreate, UserOut
from app.schemas.auth import SSOExchangeRequest, DevLoginRequest, TokenResponse
from app.schemas.course import (
    InstructorPublic,
    LanguageSummary,
    InstructorLanguageSummary,
    CourseResource,
    CourseResourceCreate,
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
from app.schemas.instructor import InstructorProfileIn, InstructorProfileOut
from app.schemas.streak import UserStreakOut, UserStreakHeartbeatIn
from app.schemas.article import ArticleOut, ArticleCreate
from app.schemas.career import JobPostingOut, JobPostingCreate, JobApplyRequest
from app.schemas.practice import (
    PracticeLabOut,
    ProgressStats,
    PracticeProgressResponse,
    PracticeEvaluateRequest,
    PracticeEvaluateResponse,
)
from app.schemas.challenge import ChallengeOut, LeaderboardEntryOut
from app.schemas.certification import (
    CertificationOut,
    CertificationVerifyRequest,
    CertificationVerifyResponse,
)
from app.schemas.admin import (
    AdminStatsOut,
    AdminUserOut,
    AdminUsersListOut,
    UserRoleUpdate,
    UserStatusUpdate,
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
    "CourseResource",
    "CourseResourceCreate",
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
    "InstructorProfileIn",
    "InstructorProfileOut",
    "UserStreakOut",
    "UserStreakHeartbeatIn",
    "ArticleOut",
    "ArticleCreate",
    "JobPostingOut",
    "JobPostingCreate",
    "JobApplyRequest",
    "PracticeLabOut",
    "ProgressStats",
    "PracticeProgressResponse",
    "PracticeEvaluateRequest",
    "PracticeEvaluateResponse",
    "ChallengeOut",
    "LeaderboardEntryOut",
    "CertificationOut",
    "CertificationVerifyRequest",
    "CertificationVerifyResponse",
    "AdminStatsOut",
    "AdminUserOut",
    "AdminUsersListOut",
    "UserRoleUpdate",
    "UserStatusUpdate",
]
