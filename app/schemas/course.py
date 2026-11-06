# app/schemas/course.py
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# --- Course Resource Schemas ---
class CourseResource(BaseModel):
    id: str
    type: str = "video"  # "video" | "pdf" | "article" | "audio" | "practice_lab"
    title: str
    url: str
    duration: Optional[str] = None
    description: Optional[str] = None


class CourseResourceCreate(BaseModel):
    type: str = "video"
    title: str
    url: str
    duration: Optional[str] = None
    description: Optional[str] = None


# --- Instructor Public Profile for Course Cards ---
class InstructorPublic(BaseModel):
    id: UUID
    full_name: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# --- Language & Instructor Hierarchy Summaries ---
class LanguageSummary(BaseModel):
    language: str
    course_count: int


class InstructorLanguageSummary(BaseModel):
    instructor_id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    course_count: int


# --- Lesson Schemas ---
class LessonBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    youtube_video_id: Optional[str] = Field(None, max_length=100)
    notes_url: Optional[str] = Field(None, max_length=500)
    order_index: int = 1
    is_preview: bool = False


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    youtube_video_id: Optional[str] = Field(None, max_length=100)
    notes_url: Optional[str] = Field(None, max_length=500)
    order_index: Optional[int] = None
    is_preview: Optional[bool] = None


class LessonOut(BaseModel):
    id: UUID
    module_id: UUID
    title: str
    description: Optional[str] = None
    youtube_video_id: Optional[str] = None  # Masked if gated
    notes_url: Optional[str] = None         # Masked if gated
    order_index: int
    is_preview: bool
    is_unlocked: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Module Schemas ---
class ModuleBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    order_index: int = 1


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    order_index: Optional[int] = None


class ModuleOut(ModuleBase):
    id: UUID
    course_id: UUID
    lessons: List[LessonOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Course Schemas ---
# Price column is Numeric(10, 2): anything above this would overflow it
MAX_PRICE = Decimal("99999999.99")


class CourseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = None
    language: str = Field(..., min_length=2, max_length=50)
    level: str = Field("foundation", max_length=30)
    category: str = Field("grammar", max_length=50)
    duration: Optional[str] = "8 Weeks"
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), le=MAX_PRICE)
    tags: List[str] = []
    resources: List[CourseResource] = []


class CourseCreate(CourseBase):
    modules: Optional[int] = 10
    # Instructors always create drafts regardless of this flag; only admins can publish directly.
    isPublished: Optional[bool] = False
    is_featured: Optional[bool] = False


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None
    language: Optional[str] = Field(None, min_length=2, max_length=50)
    level: Optional[str] = Field(None, max_length=30)
    category: Optional[str] = Field(None, max_length=50)
    duration: Optional[str] = None
    modules: Optional[int] = None
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    price: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=MAX_PRICE)
    tags: Optional[List[str]] = None
    resources: Optional[List[CourseResource]] = None
    isPublished: Optional[bool] = None
    is_published: Optional[bool] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


class CourseStatusUpdate(BaseModel):
    # Instructors can only move a course back to "draft"; the endpoint enforces that.
    # Publishing goes through submit (instructor) + approve (admin).
    status: str = Field(..., pattern="^(draft|published|archived)$")


# Brief card view for catalogs / lists
class CourseOut(CourseBase):
    id: UUID
    _id: Optional[str] = None
    instructor_id: UUID
    instructor: InstructorPublic
    status: str  # draft | pending_review | published | rejected | archived
    is_free: bool
    isPublished: bool = False
    is_published: bool = False
    is_featured: bool = False
    modules_count: int = 0
    lessons_count: int = 0
    enrolledCount: int = 0
    enrolled_count: int = 0
    # Approval workflow
    rejection_reason: Optional[str] = None
    submitted_at: Optional[datetime] = None
    managed_by_admin: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Detailed view with syllabus (modules & lessons)
class CourseDetailOut(CourseOut):
    modules: List[ModuleOut] = []