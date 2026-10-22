from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


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
    youtube_video_id: Optional[str] = Field(None, max_length=50)
    notes_url: Optional[str] = Field(None, max_length=500)
    order_index: int = 1
    is_preview: bool = False


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    youtube_video_id: Optional[str] = Field(None, max_length=50)
    notes_url: Optional[str] = Field(None, max_length=500)
    order_index: Optional[int] = None
    is_preview: Optional[bool] = None


class LessonOut(BaseModel):
    id: UUID
    module_id: UUID
    title: str
    description: Optional[str] = None
    youtube_video_id: Optional[str] = None  # None if gated / not unlocked
    notes_url: Optional[str] = None         # None if gated / not unlocked
    order_index: int
    is_preview: bool
    is_unlocked: bool = False               # True if student enrolled, preview, or owner
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
class CourseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = None
    language: str = Field(..., min_length=2, max_length=50)
    level: str = Field("Beginner", max_length=30)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None
    language: Optional[str] = Field(None, min_length=2, max_length=50)
    level: Optional[str] = Field(None, max_length=30)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))


class CourseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|published|archived)$")


# Brief card view for catalogs / lists
class CourseOut(CourseBase):
    id: UUID
    instructor_id: UUID
    instructor: InstructorPublic
    status: str
    is_free: bool
    modules_count: int = 0
    lessons_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Detailed view with syllabus (modules & lessons)
class CourseDetailOut(CourseOut):
    modules: List[ModuleOut] = []
